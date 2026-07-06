"""
Challenge: MicroVM Lifecycle Policy Engine

Implement a policy engine that decides when to suspend, resume, or terminate
a MicroVM based on its current state and idle duration. This is the kind of
logic a real orchestrator runs to manage cost and availability.
"""


def should_suspend(idle_seconds: float, max_idle_duration: int, current_state: str) -> bool:
    """
    Decide whether a MicroVM should be suspended.

    Args:
        idle_seconds: How long the MicroVM has been idle (no requests).
        max_idle_duration: The configured maxIdleDurationSeconds threshold.
        current_state: Current MicroVM state ("RUNNING", "SUSPENDED", "PENDING", "TERMINATED").

    Returns:
        True if the MicroVM should be suspended, False otherwise.
        Only RUNNING MicroVMs can be suspended.
    """
    raise NotImplementedError


def should_terminate(
    suspended_seconds: float, suspended_duration_limit: int, current_state: str
) -> bool:
    """
    Decide whether a suspended MicroVM should be terminated.

    Args:
        suspended_seconds: How long the MicroVM has been in SUSPENDED state.
        suspended_duration_limit: The configured suspendedDurationSeconds threshold.
        current_state: Current MicroVM state.

    Returns:
        True if the MicroVM should be terminated, False otherwise.
        Only SUSPENDED MicroVMs can be terminated by this policy.
    """
    raise NotImplementedError


def should_auto_resume(
    current_state: str, has_incoming_request: bool, auto_resume_enabled: bool
) -> bool:
    """
    Decide whether a suspended MicroVM should be auto-resumed.

    Args:
        current_state: Current MicroVM state.
        has_incoming_request: Whether there is a pending incoming request.
        auto_resume_enabled: Whether auto-resume is configured.

    Returns:
        True if the MicroVM should be resumed, False otherwise.
    """
    raise NotImplementedError


def compute_lifecycle_action(
    state: str,
    idle_seconds: float,
    suspended_seconds: float,
    has_incoming_request: bool,
    policy: dict,
) -> str:
    """
    Given the full state of a MicroVM and its idle policy, determine the
    next lifecycle action to take.

    Args:
        state: Current state ("RUNNING", "SUSPENDED", "PENDING", "TERMINATED").
        idle_seconds: Seconds since last activity (relevant when RUNNING).
        suspended_seconds: Seconds in SUSPENDED state (relevant when SUSPENDED).
        has_incoming_request: Whether a request is waiting.
        policy: Dict with keys "maxIdleDurationSeconds", "suspendedDurationSeconds",
                "autoResumeEnabled".

    Returns:
        One of: "SUSPEND", "TERMINATE", "RESUME", "NONE"
    """
    raise NotImplementedError
