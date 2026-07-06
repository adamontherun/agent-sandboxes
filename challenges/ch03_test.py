"""Tests for the MicroVM Lifecycle State Machine (Chapter 3 Challenge)."""

import os
import sys

import pytest

# Allow importing from challenges/ or solutions/
sys.path.insert(0, os.path.dirname(__file__))


def get_lifecycle_class():
    """Import MicrovmLifecycle - tries solution first if env var set."""
    if os.environ.get("USE_SOLUTION"):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solutions"))
        from ch03 import InvalidTransitionError, MicrovmLifecycle
    else:
        from ch03 import InvalidTransitionError, MicrovmLifecycle
    return MicrovmLifecycle, InvalidTransitionError


MicrovmLifecycle, InvalidTransitionError = get_lifecycle_class()


def suspended_vm():
    """Return a MicroVM driven to the SUSPENDED state."""
    vm = MicrovmLifecycle()
    vm.run()
    vm.suspend()
    vm.suspend_complete()
    return vm


class TestInitialState:
    def test_starts_in_pending(self):
        vm = MicrovmLifecycle()
        assert vm.state == "PENDING"


class TestValidTransitions:
    def test_pending_to_running(self):
        vm = MicrovmLifecycle()
        vm.run()
        assert vm.state == "RUNNING"

    def test_running_to_suspending(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.suspend()
        assert vm.state == "SUSPENDING"

    def test_suspending_to_suspended(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.suspend()
        vm.suspend_complete()
        assert vm.state == "SUSPENDED"

    def test_suspended_to_running(self):
        vm = suspended_vm()
        vm.resume()
        assert vm.state == "RUNNING"

    def test_running_to_terminating(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        assert vm.state == "TERMINATING"

    def test_suspended_to_terminating(self):
        vm = suspended_vm()
        vm.terminate()
        assert vm.state == "TERMINATING"

    def test_terminating_to_terminated(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        vm.terminate_complete()
        assert vm.state == "TERMINATED"


class TestInvalidTransitions:
    def test_cannot_suspend_from_pending(self):
        vm = MicrovmLifecycle()
        with pytest.raises(InvalidTransitionError) as exc_info:
            vm.suspend()
        assert exc_info.value.current_state == "PENDING"
        assert exc_info.value.action == "suspend"

    def test_cannot_terminate_from_pending(self):
        vm = MicrovmLifecycle()
        with pytest.raises(InvalidTransitionError):
            vm.terminate()

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

    def test_cannot_terminate_while_suspending(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.suspend()  # now SUSPENDING
        with pytest.raises(InvalidTransitionError):
            vm.terminate()

    def test_cannot_do_anything_from_terminated(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        vm.terminate_complete()
        for action in (vm.run, vm.suspend, vm.suspend_complete, vm.resume, vm.terminate):
            with pytest.raises(InvalidTransitionError):
                action()


class TestValidTransitionsMethod:
    def test_pending_valid_transitions(self):
        vm = MicrovmLifecycle()
        assert vm.valid_transitions() == ["run"]

    def test_running_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        assert sorted(vm.valid_transitions()) == ["suspend", "terminate"]

    def test_suspending_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.suspend()
        assert vm.valid_transitions() == ["suspend_complete"]

    def test_suspended_valid_transitions(self):
        vm = suspended_vm()
        assert sorted(vm.valid_transitions()) == ["resume", "terminate"]

    def test_terminating_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        assert vm.valid_transitions() == ["terminate_complete"]

    def test_terminated_valid_transitions(self):
        vm = MicrovmLifecycle()
        vm.run()
        vm.terminate()
        vm.terminate_complete()
        assert vm.valid_transitions() == []


class TestFullLifecyclePath:
    def test_full_cycle_with_resume(self):
        """Full lifecycle: pending -> run -> suspend -> resume -> terminate."""
        vm = MicrovmLifecycle()
        assert vm.state == "PENDING"

        vm.run()
        assert vm.state == "RUNNING"

        vm.suspend()
        assert vm.state == "SUSPENDING"

        vm.suspend_complete()
        assert vm.state == "SUSPENDED"

        vm.resume()
        assert vm.state == "RUNNING"

        vm.terminate()
        assert vm.state == "TERMINATING"

        vm.terminate_complete()
        assert vm.state == "TERMINATED"
