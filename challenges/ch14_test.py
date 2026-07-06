"""Tests for Chapter 14 challenge: a production-ready orchestrator."""

import pytest
from ch14 import ProductionOrchestrator, TransientLaunchError


@pytest.fixture
def orchestrator():
    return ProductionOrchestrator(live_version="13.0")


class TestInit:
    def test_live_version_set(self, orchestrator):
        assert orchestrator.live_version == "13.0"

    def test_no_candidate_initially(self, orchestrator):
        assert orchestrator.candidate_version is None


class TestStageCandidate:
    def test_sets_candidate_version(self, orchestrator):
        orchestrator.stage_candidate("14.0")
        assert orchestrator.candidate_version == "14.0"


class TestLaunchWithRetry:
    def test_succeeds_first_try(self, orchestrator):
        def launch_fn(version):
            return {"microvmId": "m-1", "state": "RUNNING", "imageVersion": version}

        result = orchestrator.launch_with_retry(launch_fn, "14.0")
        assert result["state"] == "RUNNING"
        assert len(orchestrator.attempts) == 1
        assert orchestrator.attempts[0].succeeded is True
        assert orchestrator.attempts[0].attempt == 1

    def test_retries_transient_failures(self, orchestrator):
        calls = {"count": 0}

        def launch_fn(version):
            calls["count"] += 1
            if calls["count"] < 3:
                raise TransientLaunchError("throttled")
            return {"microvmId": "m-1", "state": "RUNNING", "imageVersion": version}

        result = orchestrator.launch_with_retry(launch_fn, "14.0")
        assert result["state"] == "RUNNING"
        assert calls["count"] == 3
        assert len(orchestrator.attempts) == 3
        assert [a.succeeded for a in orchestrator.attempts] == [False, False, True]
        assert [a.attempt for a in orchestrator.attempts] == [1, 2, 3]

    def test_raises_after_max_attempts(self, orchestrator):
        def launch_fn(version):
            raise TransientLaunchError("throttled")

        with pytest.raises(RuntimeError):
            orchestrator.launch_with_retry(launch_fn, "14.0", max_attempts=3)
        assert len(orchestrator.attempts) == 3
        assert all(not a.succeeded for a in orchestrator.attempts)

    def test_records_image_version_on_attempts(self, orchestrator):
        def launch_fn(version):
            return {"state": "RUNNING"}

        orchestrator.launch_with_retry(launch_fn, "14.0")
        assert orchestrator.attempts[0].image_version == "14.0"


class TestCutOver:
    def test_raises_without_staged_candidate(self, orchestrator):
        with pytest.raises(ValueError):
            orchestrator.cut_over({"state": "RUNNING"})

    def test_healthy_running_cuts_over(self, orchestrator):
        orchestrator.stage_candidate("14.0")
        result = orchestrator.cut_over({"state": "RUNNING"})
        assert result is True
        assert orchestrator.live_version == "14.0"
        assert orchestrator.candidate_version is None

    def test_healthy_suspended_cuts_over(self, orchestrator):
        orchestrator.stage_candidate("14.0")
        result = orchestrator.cut_over({"state": "SUSPENDED"})
        assert result is True
        assert orchestrator.live_version == "14.0"

    def test_terminated_aborts_cutover(self, orchestrator):
        orchestrator.stage_candidate("14.0")
        result = orchestrator.cut_over({"state": "TERMINATED"})
        assert result is False
        assert orchestrator.live_version == "13.0"
        assert orchestrator.candidate_version == "14.0"

    def test_failed_aborts_cutover(self, orchestrator):
        orchestrator.stage_candidate("14.0")
        result = orchestrator.cut_over({"state": "FAILED"})
        assert result is False
        assert orchestrator.live_version == "13.0"


class TestDecideScalingAction:
    def test_launch_when_none_running_and_queued(self, orchestrator):
        assert orchestrator.decide_scaling_action(0, 3) == "launch"

    def test_launch_when_backlog_exceeds_threshold(self, orchestrator):
        assert orchestrator.decide_scaling_action(2, 15) == "launch"

    def test_scale_down_when_idle(self, orchestrator):
        assert orchestrator.decide_scaling_action(3, 0) == "scale_down"

    def test_hold_when_balanced(self, orchestrator):
        assert orchestrator.decide_scaling_action(2, 4) == "hold"

    def test_hold_single_running_no_queue(self, orchestrator):
        assert orchestrator.decide_scaling_action(1, 0) == "hold"
