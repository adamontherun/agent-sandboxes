"""
Challenge: build a minimal AI code assistant tool-calling loop.

Implement a ToolCallRouter that dispatches structured LLM "tool calls" against
a Session-like sandbox object (see examples/ch15_repl_session.py for the real
Session this simulates the same shape as) and turns each result into a
tool_result-style dict ready to feed back into an LLM conversation, plus
tracks a simple turn budget for a long-running development session.
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
    """Dispatches ToolCall objects to a sandbox and tracks a turn budget.

    Must support:
      - __init__(sandbox, max_turns=20)
            Stores sandbox and max_turns. Sets self.turns_used to 0.
      - dispatch(call: ToolCall) -> dict
            Increments self.turns_used by 1. If self.turns_used exceeds
            max_turns, raises TurnBudgetExceeded before doing anything else
            (the turn that exceeds the budget doesn't get dispatched).
            Otherwise routes call.name to the matching sandbox method:
              - "write_file" -> sandbox.write_file(**call.arguments)
              - "read_file"  -> sandbox.read_file(**call.arguments)
              - "run_command" -> sandbox.run_command(**call.arguments)
            Any other call.name raises ValueError(f"unknown tool: {call.name}").
            Wraps the sandbox method's return value (an object with .ok,
            .output, .detail attributes) into a tool_result-shaped dict:
              {"tool": call.name, "ok": <ok>, "output": <output>}
      - remaining_turns() -> int
            Returns max_turns - turns_used (can be negative if exceeded,
            though dispatch() itself always raises before that happens).
    """

    def __init__(self, sandbox, max_turns: int = 20):
        raise NotImplementedError("Implement ToolCallRouter.__init__()")

    def dispatch(self, call: ToolCall) -> dict:
        raise NotImplementedError("Implement ToolCallRouter.dispatch()")

    def remaining_turns(self) -> int:
        raise NotImplementedError("Implement ToolCallRouter.remaining_turns()")
