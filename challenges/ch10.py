"""
Challenge: Resource limit evaluation for execution requests.

Implement evaluate_request() to enforce a ResourcePolicy against
incoming ExecutionRequests. See book/chapters/ch10.html for details.
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

    Rules:
      - If code contains any blocked_patterns, deny with a reason.
      - If code exceeds max_code_size_bytes (UTF-8), deny with a reason.
      - If timeout is outside [min, max], clamp it and report in adjusted_timeout.
      - If memory is outside [min, max], clamp it and report in adjusted_memory.
      - Otherwise allow.
    """
    raise NotImplementedError("Implement evaluate_request()")
