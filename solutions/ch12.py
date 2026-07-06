"""
Solution: pre-execution static scanner for untrusted Python code.
"""

import ast
from dataclasses import dataclass, field


@dataclass
class ScanResult:
    """Result of scanning one snippet of code."""
    safe: bool
    violations: list[str] = field(default_factory=list)


DANGEROUS_IMPORTS = {"ctypes", "cffi"}

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

DANGEROUS_BUILTINS = {"eval", "exec", "__import__"}


class _Visitor(ast.NodeVisitor):
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
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                self.violations.append(f"line {node.lineno}: 'shell=True' is blocked")
        self.generic_visit(node)

    @staticmethod
    def _qualified_name(node: ast.expr) -> str | None:
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
            return ".".join(reversed(parts))
        return None


class SandboxHardener:
    """Scans untrusted Python source for known-dangerous patterns."""

    def scan(self, source: str) -> ScanResult:
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return ScanResult(safe=False, violations=[f"syntax error: {exc}"])

        visitor = _Visitor()
        visitor.visit(tree)
        return ScanResult(safe=not visitor.violations, violations=visitor.violations)
