"""
Runnable example: demonstrate ResourcePolicy evaluation across scenarios.

No AWS calls; imports the reference solution and runs several requests
through evaluate_request() to show allow/deny/clamp behavior.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "solutions"))

from ch10 import ExecutionRequest, ResourcePolicy, evaluate_request


def show(label: str, req: ExecutionRequest, policy: ResourcePolicy) -> None:
    decision = evaluate_request(req, policy)
    print(f"\n[{label}]")
    print(
        f"  request: timeout={req.timeout_seconds}s "
        f"memory={req.memory_mb}MB code_len={len(req.code)}"
    )
    print(f"  allowed: {decision.allowed}")
    if decision.reason:
        print(f"  reason:  {decision.reason}")
    if decision.adjusted_timeout is not None:
        print(f"  clamped timeout -> {decision.adjusted_timeout}s")
    if decision.adjusted_memory is not None:
        print(f"  clamped memory  -> {decision.adjusted_memory}MB")


def main() -> None:
    policy = ResourcePolicy()

    show(
        "normal request",
        ExecutionRequest(code='print("hello")', timeout_seconds=5.0, memory_mb=256),
        policy,
    )

    show(
        "python fork bomb",
        ExecutionRequest(code="import os\nwhile True: os.fork()", timeout_seconds=5.0),
        policy,
    )

    show(
        "bash fork bomb",
        ExecutionRequest(code=":(){ :|:& };:", timeout_seconds=5.0),
        policy,
    )

    show(
        "oversized code",
        ExecutionRequest(code="x = 1\n" * 30_000, timeout_seconds=5.0),
        policy,
    )

    show(
        "timeout too high (clamped)",
        ExecutionRequest(code='print("hi")', timeout_seconds=600.0),
        policy,
    )

    show(
        "memory too high (clamped)",
        ExecutionRequest(code='print("hi")', timeout_seconds=5.0, memory_mb=4096),
        policy,
    )

    show(
        "both bounds too low (clamped)",
        ExecutionRequest(code='print("hi")', timeout_seconds=0.05, memory_mb=8),
        policy,
    )

    strict = ResourcePolicy(
        max_timeout_seconds=10.0,
        max_memory_mb=128,
        blocked_patterns=["eval(", "exec(", "__import__"],
    )
    show(
        "strict policy blocks eval()",
        ExecutionRequest(code='eval("2+2")', timeout_seconds=5.0),
        strict,
    )


if __name__ == "__main__":
    main()
