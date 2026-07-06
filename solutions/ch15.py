"""
Solution: a minimal AI code assistant tool-calling loop, dispatching
structured tool calls against a sandbox and tracking a turn budget.
"""

from dataclasses import dataclass


class TurnBudgetExceeded(Exception):
    """Raised when a session has exhausted its allotted turns."""


@dataclass
class ToolCall:
    """One LLM-issued tool call."""

    name: str
    arguments: dict


class ToolCallRouter:
    """Dispatches ToolCall objects to a sandbox and tracks a turn budget."""

    def __init__(self, sandbox, max_turns: int = 20):
        self.sandbox = sandbox
        self.max_turns = max_turns
        self.turns_used = 0

    def dispatch(self, call: ToolCall) -> dict:
        self.turns_used += 1
        if self.turns_used > self.max_turns:
            raise TurnBudgetExceeded(f"turn budget of {self.max_turns} exceeded")

        if call.name == "write_file":
            result = self.sandbox.write_file(**call.arguments)
        elif call.name == "read_file":
            result = self.sandbox.read_file(**call.arguments)
        elif call.name == "run_command":
            result = self.sandbox.run_command(**call.arguments)
        else:
            raise ValueError(f"unknown tool: {call.name}")

        return {"tool": call.name, "ok": result.ok, "output": result.output}

    def remaining_turns(self) -> int:
        return self.max_turns - self.turns_used
