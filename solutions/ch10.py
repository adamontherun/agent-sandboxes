"""
Solution: Resource limit evaluation for execution requests.
"""

from dataclasses import dataclass, field


@dataclass
class ExecutionRequest:
    """A request to execute code with resource requirements."""

    code: str
    timeout_seconds: float
    memory_mb: int = 256


@dataclass
class ResourcePolicy:
    """Policy defining acceptable resource bounds."""

    max_timeout_seconds: float = 30.0
    min_timeout_seconds: float = 1.0
    max_memory_mb: int = 512
    min_memory_mb: int = 64
    max_code_size_bytes: int = 100_000
    blocked_patterns: list[str] = field(
        default_factory=lambda: ["os.fork", "fork()", ":(){ :|:& };:"]
    )


@dataclass
class PolicyDecision:
    """Result of evaluating an execution request against a policy."""

    allowed: bool
    reason: str = ""
    adjusted_timeout: float | None = None
    adjusted_memory: int | None = None


def evaluate_request(request: ExecutionRequest, policy: ResourcePolicy) -> PolicyDecision:
    """
    Evaluate an execution request against a resource policy.

    Checks for blocked patterns and code size (hard denials), then clamps
    timeout and memory to policy bounds (soft adjustments).
    """
    for pattern in policy.blocked_patterns:
        if pattern in request.code:
            return PolicyDecision(
                allowed=False,
                reason=f"Code contains blocked pattern: {pattern!r}",
            )

    code_size = len(request.code.encode("utf-8"))
    if code_size > policy.max_code_size_bytes:
        return PolicyDecision(
            allowed=False,
            reason=f"Code size {code_size} bytes exceeds limit of {policy.max_code_size_bytes}",
        )

    adjusted_timeout = None
    if request.timeout_seconds > policy.max_timeout_seconds:
        adjusted_timeout = policy.max_timeout_seconds
    elif request.timeout_seconds < policy.min_timeout_seconds:
        adjusted_timeout = policy.min_timeout_seconds

    adjusted_memory = None
    if request.memory_mb > policy.max_memory_mb:
        adjusted_memory = policy.max_memory_mb
    elif request.memory_mb < policy.min_memory_mb:
        adjusted_memory = policy.min_memory_mb

    return PolicyDecision(
        allowed=True,
        reason="",
        adjusted_timeout=adjusted_timeout,
        adjusted_memory=adjusted_memory,
    )
