"""
Chapter 3 Challenge: MicroVM Lifecycle State Machine

Model the real Lambda MicroVM lifecycle as reported by get-microvm. A MicroVM
moves through these states, including the transient SUSPENDING/TERMINATING
states the service passes through while running hooks:

    PENDING --run--> RUNNING --suspend--> SUSPENDING --suspend_complete--> SUSPENDED
                        ^                                                      |
                        |------------------- resume ---------------------------|

Valid transitions (see the state table in Chapter 3):

    PENDING      --run-->                RUNNING
    RUNNING      --suspend-->            SUSPENDING
    RUNNING      --terminate-->          TERMINATING
    SUSPENDING   --suspend_complete-->   SUSPENDED
    SUSPENDED    --resume-->             RUNNING
    SUSPENDED    --terminate-->          TERMINATING
    TERMINATING  --terminate_complete--> TERMINATED
    TERMINATED   (terminal state)
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

    def __init__(self):
        raise NotImplementedError

    def run(self) -> None:
        raise NotImplementedError

    def suspend(self) -> None:
        raise NotImplementedError

    def suspend_complete(self) -> None:
        raise NotImplementedError

    def resume(self) -> None:
        raise NotImplementedError

    def terminate(self) -> None:
        raise NotImplementedError

    def terminate_complete(self) -> None:
        raise NotImplementedError

    def valid_transitions(self) -> list[str]:
        raise NotImplementedError
