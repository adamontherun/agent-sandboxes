"""
Chapter 3 Solution: MicroVM Lifecycle State Machine
"""


class InvalidTransitionError(Exception):
    """Raised when a state transition is not allowed from the current state."""

    def __init__(self, current_state: str, action: str):
        self.current_state = current_state
        self.action = action
        super().__init__(
            f"Cannot '{action}' from state '{current_state}'"
        )


class MicrovmLifecycle:
    """Models the lifecycle state machine of a Lambda MicroVM."""

    CREATING = "CREATING"
    RUNNING = "RUNNING"
    IDLE = "IDLE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"

    # Transition table: state -> {action: next_state}
    _TRANSITIONS = {
        "CREATING": {"run": "RUNNING"},
        "RUNNING": {"idle": "IDLE", "terminate": "TERMINATED"},
        "IDLE": {"suspend": "SUSPENDED", "terminate": "TERMINATED"},
        "SUSPENDED": {"resume": "RUNNING", "terminate": "TERMINATED"},
        "TERMINATED": {},
    }

    def __init__(self):
        self.state = self.CREATING

    def _transition(self, action: str) -> None:
        allowed = self._TRANSITIONS.get(self.state, {})
        if action not in allowed:
            raise InvalidTransitionError(self.state, action)
        self.state = allowed[action]

    def run(self) -> None:
        self._transition("run")

    def idle(self) -> None:
        self._transition("idle")

    def suspend(self) -> None:
        self._transition("suspend")

    def resume(self) -> None:
        self._transition("resume")

    def terminate(self) -> None:
        self._transition("terminate")

    def valid_transitions(self) -> list[str]:
        return list(self._TRANSITIONS.get(self.state, {}).keys())
