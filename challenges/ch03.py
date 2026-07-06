"""
Chapter 3 Challenge: MicroVM Lifecycle State Machine
"""


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed from the current state."""

    def __init__(self, current_state: str, action: str):
        self.current_state = current_state
        self.action = action
        super().__init__(f"Cannot '{action}' from state '{current_state}'")


class MicrovmLifecycle:
    """Models the lifecycle state machine of a Lambda MicroVM."""

    CREATING = "CREATING"
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"

    def __init__(self):
        raise NotImplementedError

    def run(self) -> None:
        raise NotImplementedError

    def idle(self) -> None:
        raise NotImplementedError

    def suspend(self) -> None:
        raise NotImplementedError

    def resume(self) -> None:
        raise NotImplementedError

    def terminate(self) -> None:
        raise NotImplementedError

    def valid_transitions(self) -> list[str]:
        raise NotImplementedError
