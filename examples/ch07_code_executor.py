"""
Chapter 7 Example: A minimal code-execution endpoint.

Demonstrates the core pattern behind "run this snippet and give me the
output" — the same shape a coding-assistant sandbox uses under the hood:

    1. Receive a code snippet over HTTP (a Flask endpoint).
    2. Write it to a file on disk.
    3. Execute it in a subprocess with a timeout.
    4. Capture stdout/stderr and the exit code.
    5. Clean up the file regardless of outcome.

This script runs entirely on a local dev machine — there is no real
MicroVM here. `subprocess.run(..., timeout=...)` enforces the wall-clock
timeout the same way a real deployment would, but it does NOT give you
the MicroVM's actual isolation: no separate kernel, no memory ceiling
enforced by cgroups, no network isolation, no filesystem boundary beyond
the OS's own user permissions. Inside a real Lambda MicroVM, this same
Flask app would be the thing running *inside* the VM, and the VM (not
this code) is what stops a malicious snippet from touching the host,
exhausting the host's memory, or reaching the internet. Run this file
directly (`python3 ch07_code_executor.py`) to see it exercised against
a small battery of snippets, including a couple designed to fail.
"""

import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool
    duration_seconds: float


def execute_snippet(code: str, timeout_seconds: float = 5.0) -> ExecutionResult:
    """Write `code` to a temp file, run it with `python3`, capture output.

    This is the function a Flask endpoint would call for each incoming
    request. It isolates only at the process level (a real MicroVM adds
    the VM boundary around the whole thing).
    """
    workdir = Path(tempfile.mkdtemp(prefix="ch07-exec-"))
    script_path = workdir / f"{uuid.uuid4().hex}.py"
    script_path.write_text(code)

    started = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=workdir,
        )
        stdout, stderr, exit_code = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout or ""
        stderr = (exc.stderr or "") + "\n[execution timed out]"
        exit_code = None
    finally:
        duration = time.monotonic() - started
        # Clean up regardless of success, failure, or timeout.
        script_path.unlink(missing_ok=True)
        workdir.rmdir()

    return ExecutionResult(
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        timed_out=timed_out,
        duration_seconds=round(duration, 3),
    )


try:
    from flask import Flask, jsonify, request

    app = Flask(__name__)

    @app.post("/execute")
    def execute_endpoint():
        """POST {"code": "...", "timeout_seconds": 5} -> execution result."""
        payload = request.get_json(force=True, silent=True) or {}
        code = payload.get("code", "")
        timeout_seconds = float(payload.get("timeout_seconds", 5.0))

        if not code:
            return jsonify({"error": "missing 'code' field"}), 400

        result = execute_snippet(code, timeout_seconds=timeout_seconds)
        return jsonify(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out,
                "duration_seconds": result.duration_seconds,
            }
        )

except ImportError:
    app = None  # Flask not installed; the CLI demo below still works.


SNIPPETS = [
    ("hello world", "print('hello from inside the sandbox')"),
    ("a computation", "print(sum(i * i for i in range(100)))"),
    (
        "writes to stderr",
        "import sys\nsys.stderr.write('warning: something noisy\\n')\nprint('done anyway')",
    ),
    ("a crash", "raise ValueError('this snippet intentionally throws')"),
    ("an infinite loop", "while True:\n    pass"),
]


def main() -> None:
    print("Running each snippet through execute_snippet() directly")
    print("(no HTTP layer for this demo — see the /execute Flask route")
    print("in this file for the endpoint version).\n")

    for label, code in SNIPPETS:
        print("=" * 60)
        print(f"Snippet: {label}")
        print("=" * 60)
        print(f"Code:\n{code}\n")

        timeout = 1.0 if label == "an infinite loop" else 5.0
        result = execute_snippet(code, timeout_seconds=timeout)

        print(f"exit_code:   {result.exit_code}")
        print(f"timed_out:   {result.timed_out}")
        print(f"duration_s:  {result.duration_seconds}")
        print(f"stdout:      {result.stdout.strip()!r}")
        print(f"stderr:      {result.stderr.strip()!r}")
        print()


if __name__ == "__main__":
    main()
