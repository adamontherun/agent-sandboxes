"""
Runnable example: structured logging and health checks for sandbox executions.

Demonstrates the observability patterns Chapter 13 recommends for Lambda
MicroVM workloads: structured JSON log lines (one per event, shaped for
CloudWatch Logs), request-level tracing with timing, and a health-check
function that inspects a MicroVM's state/stateReason the way GetMicrovm
returns it.

No AWS calls required - this simulates execution locally to show the log
shape and timing logic you'd wire into a real orchestrator.
"""

import json
import time
import uuid
from dataclasses import dataclass, field


@dataclass
class ExecutionResult:
    """Result of a sandboxed code execution."""
    request_id: str
    status: str  # "success", "error", "timeout"
    output: str = ""
    error: str = ""
    duration_ms: float = 0.0


def structured_log(event: str, **kwargs) -> None:
    """Emit a single structured JSON log line to stdout.

    In production, stdout from a MicroVM's application process is what
    CloudWatch Logs captures - each line becomes one log event in the
    stream. Structured JSON lets Logs Insights query individual fields
    without regex parsing.
    """
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
        **kwargs,
    }
    print(json.dumps(entry))


def execute_sandboxed_code(code: str, timeout_seconds: float = 5.0) -> ExecutionResult:
    """Execute code with structured logging around the entire lifecycle.

    This is the pattern: bracket every execution with start/end log lines
    carrying the same request_id, so CloudWatch Logs Insights can correlate
    them with `filter request_id = "..."` and immediately see duration,
    status, and any error without reading the full stream.
    """
    request_id = str(uuid.uuid4())

    structured_log(
        "execution.start",
        request_id=request_id,
        code_length=len(code),
        timeout_seconds=timeout_seconds,
    )

    start = time.perf_counter()

    try:
        # Simulate execution (in production this would be an HTTP call
        # to the MicroVM's code-execution endpoint)
        namespace = {}
        safe_builtins = {"sum": sum, "range": range, "len": len, "int": int,
                         "float": float, "str": str, "list": list, "dict": dict,
                         "min": min, "max": max, "abs": abs, "round": round}
        exec(code, {"__builtins__": safe_builtins}, namespace)
        output = str(namespace.get("result", ""))
        status = "success"
        error = ""
    except Exception as exc:
        output = ""
        status = "error"
        error = f"{type(exc).__name__}: {exc}"

    duration_ms = (time.perf_counter() - start) * 1000

    structured_log(
        "execution.end",
        request_id=request_id,
        status=status,
        duration_ms=round(duration_ms, 2),
        error=error or None,
    )

    return ExecutionResult(
        request_id=request_id,
        status=status,
        output=output,
        error=error,
        duration_ms=duration_ms,
    )


def check_microvm_health(microvm_state: dict) -> dict:
    """Inspect a MicroVM's state from GetMicrovm response fields.

    In production you'd call GetMicrovm and inspect the response; here we
    accept the relevant fields as a dict to demonstrate the logic without
    an AWS call. The real response includes `state`, `stateReason`, and
    (when applicable) `terminatedAt`.

    Real example from a terminated instance:
        {"state": "TERMINATED", "stateReason": "Success.",
         "terminatedAt": "2026-07-05T21:47:36.936000-10:00"}
    """
    state = microvm_state.get("state", "UNKNOWN")
    state_reason = microvm_state.get("stateReason", "")

    healthy = state in ("RUNNING", "SUSPENDED")
    needs_attention = state in ("TERMINATED", "FAILED", "UNKNOWN")

    result = {
        "healthy": healthy,
        "state": state,
        "stateReason": state_reason,
        "action": "none" if healthy else "investigate",
    }

    structured_log(
        "health_check",
        microvm_state=state,
        healthy=healthy,
        state_reason=state_reason,
    )

    return result


if __name__ == "__main__":
    print("=== Structured Logging Demo ===\n")

    # Successful execution
    print("--- Successful execution ---")
    result = execute_sandboxed_code("result = sum(range(10))")
    print(f"  -> status={result.status}, output={result.output!r}, "
          f"duration={result.duration_ms:.2f}ms\n")

    # Failing execution
    print("--- Failing execution ---")
    result = execute_sandboxed_code("x = 1 / 0")
    print(f"  -> status={result.status}, error={result.error!r}\n")

    # Health check on a running instance
    print("--- Health check: running instance ---")
    health = check_microvm_health({"state": "RUNNING", "stateReason": ""})
    print(f"  -> healthy={health['healthy']}, action={health['action']}\n")

    # Health check on a terminated instance (real stateReason from GetMicrovm)
    print("--- Health check: terminated instance ---")
    health = check_microvm_health({
        "state": "TERMINATED",
        "stateReason": "Success.",
        "terminatedAt": "2026-07-05T21:47:36.936000-10:00",
    })
    print(f"  -> healthy={health['healthy']}, action={health['action']}\n")

    print("=== Done ===")
