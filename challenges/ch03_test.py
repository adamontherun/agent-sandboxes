"""Tests for the MicroVM Lifecycle State Machine (Chapter 3 Challenge)."""

import pytest
import sys
import os

# Allow importing from challenges/ or solutions/
sys.path.insert(0, os.path.dirname(__file__))


def get_lifecycle_class():
    """Import MicrovmLifecycle - tries solution first if env var set."""
    if os.environ.get("USE_SOLUTION"):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solutions"))
        from ch03 import MicrovmLifecycle, InvalidTransitionError
    else:
        from ch03 import MicrovmLifecycle, InvalidTransitionError
    return MicrovmLifecycle, InvalidTransitionError


MicrovmLifecycle, InvalidTransitionError = get_lifecycle_class()


class TestInitialState:
    def test_starts_in_creating(self):
        vm = MicrovmLifecycle()
        assert vm.state == "CREATING"


class TestValidTransitions:
    def test_creating_to_running(self):
        vm = MicrovmLifecycle()
        vm.run()
        assert vm.state == "RUNNING"

    def test_running_to_idle(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.idle()
        assert vm.state == "IDLE"

    def test_idle_to_suspended(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.idle()
        vm.suspend()
        assert vm.state == "SUSPENDED"

    def test_suspended_to_running(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.idle()
        vm.suspend()
        vm.resume()
        assert vm.state == "RUNNING"

    def test_terminate_from_running(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        assert vm.state == "TERMINATED"

    def test_terminate_from_idle(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.idle()
        vm.terminate()
        assert vm.state == "TERMINATED"

    def test_terminate_from_suspended(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.idle()
        vm.suspend()
        vm.terminate()
        assert vm.state == "TERMINATED"


class TestInvalidTransitions:
    def test_cannot_idle_from_creating(self):
        vm = MicrovmLifecycle()
        with pytest.raises(InvalidTransitionError) as exc_info:
            vm.idle()
        assert exc_info.value.current_state == "CREATING"
        assert exc_info.value.action == "idle"

    def test_cannot_suspend_from_running(self):
        vm = MicrovmLifecycle()
        vm.run()
        with pytest.raises(InvalidTransitionError):
            vm.suspend()

    def test_cannot_resume_from_running(self):
        vm = MicrovmLifecycle()
        vm.run()
        with pytest.raises(InvalidTransitionError):
            vm.resume()

    def test_cannot_run_from_running(self):
        vm = MicrovmLifecycle()
        vm.run()
        with pytest.raises(InvalidTransitionError):
            vm.run()

    def test_cannot_do_anything_from_terminated(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        with pytest.raises(InvalidTransitionError):
            vm.run()
        with pytest.raises(InvalidTransitionError):
            vm.idle()
        with pytest.raises(InvalidTransitionError):
            vm.suspend()
        with pytest.raises(InvalidTransitionError):
            vm.resume()
        with pytest.raises(InvalidTransitionError):
            vm.terminate()

    def test_cannot_terminate_from_creating(self):
        vm = MicrovmLifecycle()
        with pytest.raises(InvalidTransitionError):
            vm.terminate()


class TestValidTransitionsMethod:
    def test_creating_valid_transitions(self):
        vm = MicrovmLifecycle()
        assert vm.valid_transitions() == ["run"]

    def test_running_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        assert sorted(vm.valid_transitions()) == ["idle", "terminate"]

    def test_idle_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.idle()
        assert sorted(vm.valid_transitions()) == ["suspend", "terminate"]

    def test_suspended_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.idle()
        vm.suspend()
        assert sorted(vm.valid_transitions()) == ["resume", "terminate"]

    def test_terminated_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        assert vm.valid_transitions() == []


class TestFullLifecyclePath:
    def test_full_cycle_with_resume(self):
        """Test the complete lifecycle: create -> run -> idle -> suspend -> resume -> idle -> terminate."""
        vm = MicrovmLifecycle()
        assert vm.state == "CREATING"

        vm.run()
        assert vm.state == "RUNNING"

        vm.idle()
        assert vm.state == "IDLE"

        vm.suspend()
        assert vm.state == "SUSPENDED"

        vm.resume()
        assert vm.state == "RUNNING"

        vm.idle()
        assert vm.state == "IDLE"

        vm.terminate()
        assert vm.state == "TERMINATED"
