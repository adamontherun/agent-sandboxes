"""
Challenge: Build a Python code executor

Implement the pieces that decide how a code-execution endpoint should
behave, without needing a real subprocess or MicroVM to test them. This
mirrors the logic in examples/ch07_code_executor.py but factors the
decision-making into pure, testable functions.
"""

from dataclasses import dataclass


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool


def validate_request(payload: dict) -> str | None:
    """
    Validate an incoming execution request payload.

    Args:
        payload: The parsed JSON body, expected to have a "code" key
            (str) and optionally a "timeout_seconds" key (number).

    Returns:
        An error message string if the payload is invalid, or None if
        it is valid. Invalid means: "code" missing, "code" is not a
        non-empty string, or "timeout_seconds" is present but not a
        positive number.
    """
    raise NotImplementedError


def build_command(script_path: str) -> list[str]:
    """
    Build the subprocess command used to execute a saved script.

    Args:
        script_path: Absolute path to the Python file to execute.

    Returns:
        The argv list to pass to subprocess.run, e.g.
        [sys.executable, script_path]. Use "python3" (not sys.executable)
        as the interpreter to keep this function dependency-free and
        deterministic for testing.
    """
    raise NotImplementedError


def summarize_result(
    stdout: str, stderr: str, exit_code: int | None, timed_out: bool
) -> ExecutionResult:
    """
    Normalize raw subprocess output into an ExecutionResult.

    Args:
        stdout: Captured standard output (may be empty).
        stderr: Captured standard error (may be empty).
        exit_code: Process exit code, or None if the process timed out
            before finishing.
        timed_out: Whether the timeout fired before completion.

    Returns:
        An ExecutionResult with the same fields, unchanged, wrapped in
        the dataclass. (This function exists as the single seam an
        endpoint calls after execution, so callers only import one
        constructor.)
    """
    raise NotImplementedError


def is_successful(result: ExecutionResult) -> bool:
    """
    Decide whether an execution should be reported as successful.

    Args:
        result: The ExecutionResult to evaluate.

    Returns:
        True only if the process did not time out and exited with
        code 0. Anything else (nonzero exit, None exit code, timeout)
        counts as unsuccessful.
    """
    raise NotImplementedError
