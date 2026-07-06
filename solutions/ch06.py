"""
Solution: MicroVM Lifecycle Policy Engine
"""


def should_suspend(idle_seconds: float, max_idle_duration: int,
                   current_state: str) -> bool:
    if current_state != "RUNNING":
        return False
    return idle_seconds >= max_idle_duration


def should_terminate(suspended_seconds: float, suspended_duration_limit: int,
                     current_state: str) -> bool:
    if current_state != "SUSPENDED":
        return False
    return suspended_seconds >= suspended_duration_limit


def should_auto_resume(current_state: str, has_incoming_request: bool,
                       auto_resume_enabled: bool) -> bool:
    if current_state != "SUSPENDED":
        return False
    return has_incoming_request and auto_resume_enabled


def compute_lifecycle_action(state: str, idle_seconds: float,
                             suspended_seconds: float,
                             has_incoming_request: bool,
                             policy: dict) -> str:
    if state == "TERMINATED" or state == "PENDING":
        return "NONE"

    if state == "RUNNING":
        if should_suspend(idle_seconds, policy["maxIdleDurationSeconds"], state):
            return "SUSPEND"
        return "NONE"

    if state == "SUSPENDED":
        # Resume takes priority over terminate
        if should_auto_resume(state, has_incoming_request, policy["autoResumeEnabled"]):
            return "RESUME"
        if should_terminate(suspended_seconds, policy["suspendedDurationSeconds"], state):
            return "TERMINATE"
        return "NONE"

    return "NONE"
