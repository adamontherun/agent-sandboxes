"""
Chapter 3 Solution: MicroVM Lifecycle State Machine
"""


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed from the current state."""

    def __init__(self, current_state: str, action: str):
        self.current_state = current_state
        self.action = action
        super().__init__(f"Cannot '{action}' from state '{current_state}'")


class MicrovmLifecycle:
    """Models the lifecycle state machine of a Lambda MicroVM."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUSPENDING = "SUSPENDING"
    SUSPENDED = "SUSPENDED"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"

    # Transition table: state -> {action: next_state}
    _TRANSITIONS = {
        "PENDING": {"run": "RUNNING"},
        "RUNNING": {"suspend": "SUSPENDING", "terminate": "TERMINATING"},
        "SUSPENDING": {"suspend_complete": "SUSPENDED"},
        "SUSPENDED": {"resume": "RUNNING", "terminate": "TERMINATING"},
        "TERMINATING": {"terminate_complete": "TERMINATED"},
        "TERMINATED": {},
    }

    def __init__(self):
        self.state = self.PENDING

    def _transition(self, action: str) -> None:
        allowed = self._TRANSITIONS.get(self.state, {})
        if action not in allowed:
            raise InvalidTransitionError(self.state, action)
        self.state = allowed[action]

    def run(self) -> None:
        self._transition("run")

    def suspend(self) -> None:
        self._transition("suspend")

    def suspend_complete(self) -> None:
        self._transition("suspend_complete")

    def resume(self) -> None:
        self._transition("resume")

    def terminate(self) -> None:
        self._transition("terminate")

    def terminate_complete(self) -> None:
        self._transition("terminate_complete")

    def valid_transitions(self) -> list[str]:
        return list(self._TRANSITIONS.get(self.state, {}).keys())
