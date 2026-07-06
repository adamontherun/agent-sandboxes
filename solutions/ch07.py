"""
Solution: Build a Python code executor
"""

from dataclasses import dataclass


@dataclass
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int | None
    timed_out: bool


def validate_request(payload: dict) -> str | None:
    code = payload.get("code")
    if not isinstance(code, str) or not code:
        return "missing or empty 'code' field"

    if "timeout_seconds" in payload:
        timeout = payload["timeout_seconds"]
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            return "'timeout_seconds' must be a positive number"
        if timeout <= 0:
            return "'timeout_seconds' must be a positive number"

    return None


def build_command(script_path: str) -> list[str]:
    return ["python3", script_path]


def summarize_result(stdout: str, stderr: str, exit_code: int | None,
                      timed_out: bool) -> ExecutionResult:
    return ExecutionResult(stdout=stdout, stderr=stderr, exit_code=exit_code, timed_out=timed_out)


def is_successful(result: ExecutionResult) -> bool:
    return not result.timed_out and result.exit_code == 0
