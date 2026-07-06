"""Tests for Chapter 15 challenge: a minimal AI code assistant tool-calling loop."""

from types import SimpleNamespace

import pytest
from ch15 import ToolCall, ToolCallRouter, TurnBudgetExceeded


class FakeSandbox:
    """Stands in for examples/ch15_repl_session.py's Session for testing
    the router in isolation from a real filesystem/subprocess.
    """

    def write_file(self, path, content):
        return SimpleNamespace(ok=True, output=f"wrote to {path}", detail={"path": path})

    def read_file(self, path):
        if path == "missing.py":
            return SimpleNamespace(
                ok=False, output="no such file: missing.py", detail={"path": path}
            )
        return SimpleNamespace(ok=True, output="print('hi')\n", detail={"path": path})

    def run_command(self, command, timeout=10.0):
        if command == "false":
            return SimpleNamespace(ok=False, output="", detail={"exit_code": 1})
        return SimpleNamespace(ok=True, output="ok\n", detail={"exit_code": 0})


@pytest.fixture
def router():
    return ToolCallRouter(FakeSandbox(), max_turns=3)


class TestInit:
    def test_no_turns_used_initially(self, router):
        assert router.turns_used == 0

    def test_remaining_turns_full_budget(self, router):
        assert router.remaining_turns() == 3


class TestDispatchWriteFile:
    def test_routes_to_write_file(self, router):
        result = router.dispatch(ToolCall("write_file", {"path": "a.py", "content": "x"}))
        assert result == {"tool": "write_file", "ok": True, "output": "wrote to a.py"}

    def test_increments_turns_used(self, router):
        router.dispatch(ToolCall("write_file", {"path": "a.py", "content": "x"}))
        assert router.turns_used == 1


class TestDispatchReadFile:
    def test_routes_to_read_file_success(self, router):
        result = router.dispatch(ToolCall("read_file", {"path": "a.py"}))
        assert result == {"tool": "read_file", "ok": True, "output": "print('hi')\n"}

    def test_routes_to_read_file_failure(self, router):
        result = router.dispatch(ToolCall("read_file", {"path": "missing.py"}))
        assert result == {"tool": "read_file", "ok": False, "output": "no such file: missing.py"}


class TestDispatchRunCommand:
    def test_routes_to_run_command_success(self, router):
        result = router.dispatch(ToolCall("run_command", {"command": "true"}))
        assert result == {"tool": "run_command", "ok": True, "output": "ok\n"}

    def test_routes_to_run_command_failure(self, router):
        result = router.dispatch(ToolCall("run_command", {"command": "false"}))
        assert result == {"tool": "run_command", "ok": False, "output": ""}


class TestUnknownTool:
    def test_raises_value_error(self, router):
        with pytest.raises(ValueError):
            router.dispatch(ToolCall("delete_universe", {}))


class TestTurnBudget:
    def test_remaining_turns_decreases(self, router):
        router.dispatch(ToolCall("write_file", {"path": "a.py", "content": "x"}))
        assert router.remaining_turns() == 2

    def test_raises_after_budget_exhausted(self, router):
        for _ in range(3):
            router.dispatch(ToolCall("write_file", {"path": "a.py", "content": "x"}))
        with pytest.raises(TurnBudgetExceeded):
            router.dispatch(ToolCall("write_file", {"path": "a.py", "content": "x"}))

    def test_exceeding_call_not_dispatched(self, router):
        for _ in range(3):
            router.dispatch(ToolCall("write_file", {"path": "a.py", "content": "x"}))
        with pytest.raises(TurnBudgetExceeded):
            router.dispatch(ToolCall("unknown_tool_but_should_not_matter", {}))
        assert router.turns_used == 4
