"""Tests for Chapter 6 challenge: MicroVM lifecycle policy engine"""

import pytest
from ch06 import should_suspend, should_terminate, should_auto_resume, compute_lifecycle_action


class TestShouldSuspend:
    def test_idle_exceeds_threshold(self):
        assert should_suspend(idle_seconds=310, max_idle_duration=300, current_state="RUNNING") is True

    def test_idle_below_threshold(self):
        assert should_suspend(idle_seconds=100, max_idle_duration=300, current_state="RUNNING") is False

    def test_idle_exactly_at_threshold(self):
        assert should_suspend(idle_seconds=300, max_idle_duration=300, current_state="RUNNING") is True

    def test_not_running_state(self):
        assert should_suspend(idle_seconds=999, max_idle_duration=300, current_state="SUSPENDED") is False

    def test_terminated_state(self):
        assert should_suspend(idle_seconds=999, max_idle_duration=300, current_state="TERMINATED") is False

    def test_pending_state(self):
        assert should_suspend(idle_seconds=999, max_idle_duration=300, current_state="PENDING") is False


class TestShouldTerminate:
    def test_suspended_exceeds_limit(self):
        assert should_terminate(suspended_seconds=310, suspended_duration_limit=300, current_state="SUSPENDED") is True

    def test_suspended_below_limit(self):
        assert should_terminate(suspended_seconds=100, suspended_duration_limit=300, current_state="SUSPENDED") is False

    def test_suspended_at_limit(self):
        assert should_terminate(suspended_seconds=300, suspended_duration_limit=300, current_state="SUSPENDED") is True

    def test_not_suspended_state(self):
        assert should_terminate(suspended_seconds=999, suspended_duration_limit=300, current_state="RUNNING") is False


class TestShouldAutoResume:
    def test_suspended_with_request_and_enabled(self):
        assert should_auto_resume("SUSPENDED", has_incoming_request=True, auto_resume_enabled=True) is True

    def test_suspended_with_request_but_disabled(self):
        assert should_auto_resume("SUSPENDED", has_incoming_request=True, auto_resume_enabled=False) is False

    def test_suspended_no_request(self):
        assert should_auto_resume("SUSPENDED", has_incoming_request=False, auto_resume_enabled=True) is False

    def test_running_with_request(self):
        assert should_auto_resume("RUNNING", has_incoming_request=True, auto_resume_enabled=True) is False


class TestComputeLifecycleAction:
    def test_running_idle_should_suspend(self):
        policy = {"maxIdleDurationSeconds": 300, "suspendedDurationSeconds": 600, "autoResumeEnabled": True}
        assert compute_lifecycle_action("RUNNING", idle_seconds=400, suspended_seconds=0,
                                        has_incoming_request=False, policy=policy) == "SUSPEND"

    def test_running_active_no_action(self):
        policy = {"maxIdleDurationSeconds": 300, "suspendedDurationSeconds": 600, "autoResumeEnabled": True}
        assert compute_lifecycle_action("RUNNING", idle_seconds=100, suspended_seconds=0,
                                        has_incoming_request=False, policy=policy) == "NONE"

    def test_suspended_should_terminate(self):
        policy = {"maxIdleDurationSeconds": 300, "suspendedDurationSeconds": 600, "autoResumeEnabled": True}
        assert compute_lifecycle_action("SUSPENDED", idle_seconds=0, suspended_seconds=700,
                                        has_incoming_request=False, policy=policy) == "TERMINATE"

    def test_suspended_should_resume(self):
        policy = {"maxIdleDurationSeconds": 300, "suspendedDurationSeconds": 600, "autoResumeEnabled": True}
        assert compute_lifecycle_action("SUSPENDED", idle_seconds=0, suspended_seconds=100,
                                        has_incoming_request=True, policy=policy) == "RESUME"

    def test_suspended_resume_disabled(self):
        policy = {"maxIdleDurationSeconds": 300, "suspendedDurationSeconds": 600, "autoResumeEnabled": False}
        assert compute_lifecycle_action("SUSPENDED", idle_seconds=0, suspended_seconds=100,
                                        has_incoming_request=True, policy=policy) == "NONE"

    def test_terminated_no_action(self):
        policy = {"maxIdleDurationSeconds": 300, "suspendedDurationSeconds": 600, "autoResumeEnabled": True}
        assert compute_lifecycle_action("TERMINATED", idle_seconds=999, suspended_seconds=999,
                                        has_incoming_request=True, policy=policy) == "NONE"

    def test_resume_takes_priority_over_terminate(self):
        """If a request arrives and auto-resume is on, resume even if over suspend limit."""
        policy = {"maxIdleDurationSeconds": 300, "suspendedDurationSeconds": 600, "autoResumeEnabled": True}
        assert compute_lifecycle_action("SUSPENDED", idle_seconds=0, suspended_seconds=700,
                                        has_incoming_request=True, policy=policy) == "RESUME"
