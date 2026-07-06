"""
Challenge: Harden your sandbox against common attacks.

Implement a pre-execution static scanner that rejects common dangerous
Python patterns before code ever reaches a MicroVM. This is the
application-level complement to the OS-level layers (KVM, seccomp, jailer)
covered in book/chapters/ch12.html - it doesn't replace them, it saves you
from launching a sandbox for code you can reject in milliseconds.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScanResult:
    """Result of scanning one snippet of code."""

    safe: bool
    violations: list[str] = field(default_factory=list)


class SandboxHardener:
    """Scans untrusted Python source for known-dangerous patterns.

    Must block, at minimum:
      - import of "ctypes" or "cffi" (raw syscall/FFI access)
      - calls to os.system, os.popen, os.fork, os.execv/execve/execl
      - calls to subprocess.Popen/call/run/check_output
      - any call with a keyword argument shell=True
      - calls to socket.socket (raw socket access)
      - calls to the builtins eval, exec, __import__

    Must allow ordinary, non-dangerous code (arithmetic, comprehensions,
    safe stdlib usage like json/math/collections) with no violations.

    A snippet that fails to parse (SyntaxError) must also be reported as
    unsafe - code that can't be parsed can't be reasoned about.
    """

    def scan(self, source: str) -> ScanResult:
        """
        Parse `source` and return a ScanResult.

        ScanResult.safe must be False iff violations is non-empty (or the
        code fails to parse). Each violation should be a human-readable
        string describing what was found and, where possible, the line
        number.
        """
        raise NotImplementedError("Implement SandboxHardener.scan()")
