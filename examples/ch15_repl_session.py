"""
Runnable example: a minimal REPL-style session loop against a SIMULATED
MicroVM boundary.

IMPORTANT — this is a LOCAL SIMULATION, not a real MicroVM: `Session` below
is a plain Python object wrapping a temp directory on this machine, and
`run_command` shells out via `subprocess` scoped to that directory. There is
no RunMicrovm call, no Firecracker, no real VM boundary here at all. The
point is to show the *shape* of the read-eval-print loop an AI coding
assistant needs on top of a real sandbox — write a file, run a command, read
a file, feed the structured result back to an LLM's tool-calling loop — using
something you can run and inspect without an AWS account. Chapters 4-14
cover the real `aws lambda-microvms` API calls (RunMicrovm, CreateMicrovmAuthToken,
GetMicrovm, and so on) that a production version of this would use as the
actual execution boundary instead of a local subprocess.
"""

from __future__ import annotations

import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ToolResult:
    """Structured result of one tool call, shaped for feeding back into an
    LLM tool-calling loop (see Chapter 15's "Integration with LLM Tool
    Calling" section for how this maps onto an actual tool_result message).
    """

    ok: bool
    output: str
    detail: dict


class Session:
    """A persistent workspace that accepts write_file / run_command /
    read_file tool calls, in the shape an AI coding assistant would issue
    them across a multi-turn conversation.

    Persistence here is just "the same temp directory survives across
    calls on this object" — the same property Chapter 3 described for a
    real MicroVM's disk across a suspend/resume cycle, but reproduced with
    an ordinary filesystem path instead of an actual VM.
    """

    def __init__(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="ch15-session-")
        self.root = Path(self._tmpdir.name).resolve()

    def write_file(self, path: str, content: str) -> ToolResult:
        target = self._resolve(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        return ToolResult(
            ok=True,
            output=f"wrote {len(content)} bytes to {path}",
            detail={"path": path, "bytes": len(content)},
        )

    def read_file(self, path: str) -> ToolResult:
        target = self._resolve(path)
        if not target.exists():
            return ToolResult(ok=False, output=f"no such file: {path}", detail={"path": path})
        content = target.read_text()
        return ToolResult(ok=True, output=content, detail={"path": path})

    def run_command(self, command: str, timeout: float = 10.0) -> ToolResult:
        try:
            proc = subprocess.run(
                shlex.split(command),
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(
                ok=False,
                output=f"command timed out after {timeout}s",
                detail={"command": command, "exit_code": None},
            )
        except FileNotFoundError as exc:
            return ToolResult(
                ok=False, output=str(exc), detail={"command": command, "exit_code": None}
            )
        ok = proc.returncode == 0
        output = proc.stdout + proc.stderr
        return ToolResult(
            ok=ok,
            output=output,
            detail={
                "command": command,
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            },
        )

    def _resolve(self, path: str) -> Path:
        # Scope every path to self.root, the way a real sandbox scopes
        # writes to the working directory (Chapter 9's filesystem
        # isolation) — this is the one line standing in for that boundary.
        resolved = (self.root / path).resolve()
        if self.root not in resolved.parents and resolved != self.root:
            raise ValueError(f"path escapes session root: {path}")
        return resolved

    def close(self) -> None:
        self._tmpdir.cleanup()


def run_repl_demo() -> None:
    """Simulate a short multi-turn coding session: write a script, run it,
    hit a bug, fix it, run it again, read the file back — the read-eval-print
    shape a coding assistant's tool-calling loop drives turn by turn.
    """
    session = Session()
    try:
        print("=== Turn 1: write a script ===")
        result = session.write_file("add.py", "print(1 + '2')\n")
        print(f"  write_file -> ok={result.ok} {result.output}")

        print("\n=== Turn 2: run it (expect failure) ===")
        result = session.run_command("python3 add.py")
        print(f"  run_command -> ok={result.ok} exit_code={result.detail['exit_code']}")
        print("  stderr:")
        for line in result.output.strip().splitlines():
            print(f"    {line}")

        print("\n=== Turn 3: fix the bug ===")
        result = session.write_file("add.py", "print(1 + int('2'))\n")
        print(f"  write_file -> ok={result.ok} {result.output}")

        print("\n=== Turn 4: run it again (expect success) ===")
        result = session.run_command("python3 add.py")
        print(f"  run_command -> ok={result.ok} exit_code={result.detail['exit_code']}")
        print(f"  stdout: {result.detail['stdout'].strip()!r}")

        print("\n=== Turn 5: read the file back (state preservation check) ===")
        result = session.read_file("add.py")
        print(f"  read_file -> ok={result.ok}")
        print(f"  content: {result.output!r}")

        print("\n=== Turn 6: reject a path that escapes the session root ===")
        try:
            session.write_file("../escape.py", "print('nope')\n")
        except ValueError as exc:
            print(f"  write_file -> raised ValueError: {exc}")
    finally:
        session.close()

    print("\n=== Done ===")


if __name__ == "__main__":
    run_repl_demo()
