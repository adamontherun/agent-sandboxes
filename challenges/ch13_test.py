"""Tests for Chapter 13 challenge: comprehensive logging for sandbox executions."""

import json

import pytest
from ch13 import ExecutionLogger, LogEntry


@pytest.fixture
def logger():
    return ExecutionLogger()


class TestLogEntry:
    def test_to_json_produces_valid_json(self):
        entry = LogEntry(
            timestamp="2026-07-06T18:00:00Z",
            event="test",
            request_id="abc-123",
            data={"foo": "bar"},
        )
        parsed = json.loads(entry.to_json())
        assert parsed["timestamp"] == "2026-07-06T18:00:00Z"
        assert parsed["event"] == "test"
        assert parsed["request_id"] == "abc-123"
        assert parsed["foo"] == "bar"

    def test_to_json_without_data(self):
        entry = LogEntry(timestamp="t", event="e", request_id="r")
        parsed = json.loads(entry.to_json())
        assert parsed == {"timestamp": "t", "event": "e", "request_id": "r"}


class TestExecutionStart:
    def test_returns_request_id(self, logger):
        rid = logger.start("x = 1")
        assert isinstance(rid, str)
        assert len(rid) > 0

    def test_unique_ids(self, logger):
        rid1 = logger.start("x = 1")
        rid2 = logger.start("x = 2")
        assert rid1 != rid2

    def test_records_start_event(self, logger):
        rid = logger.start("x = 1", timeout_seconds=10.0)
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0].event == "execution.start"
        assert logs[0].request_id == rid
        assert logs[0].data["code_length"] == 5
        assert logs[0].data["timeout_seconds"] == 10.0


class TestExecutionEnd:
    def test_records_end_event(self, logger):
        rid = logger.start("x = 1")
        logger.end(rid, status="success")
        logs = logger.get_logs()
        assert len(logs) == 2
        assert logs[1].event == "execution.end"
        assert logs[1].data["status"] == "success"

    def test_duration_is_non_negative(self, logger):
        rid = logger.start("x = 1")
        logger.end(rid, status="success")
        logs = logger.get_logs()
        assert logs[1].data["duration_ms"] >= 0

    def test_error_recorded(self, logger):
        rid = logger.start("x = 1")
        logger.end(rid, status="error", error="ZeroDivisionError")
        logs = logger.get_logs()
        assert logs[1].data["error"] == "ZeroDivisionError"

    def test_error_none_on_success(self, logger):
        rid = logger.start("x = 1")
        logger.end(rid, status="success")
        logs = logger.get_logs()
        assert logs[1].data["error"] is None


class TestHealthCheck:
    def test_running_is_healthy(self, logger):
        result = logger.health_check({"state": "RUNNING", "stateReason": ""})
        assert result["healthy"] is True
        assert result["state"] == "RUNNING"
        assert result["action"] == "none"

    def test_suspended_is_healthy(self, logger):
        result = logger.health_check({"state": "SUSPENDED", "stateReason": ""})
        assert result["healthy"] is True

    def test_terminated_is_unhealthy(self, logger):
        result = logger.health_check(
            {
                "state": "TERMINATED",
                "stateReason": "Success.",
            }
        )
        assert result["healthy"] is False
        assert result["action"] == "investigate"
        assert result["stateReason"] == "Success."

    def test_unknown_state_is_unhealthy(self, logger):
        result = logger.health_check({"state": "UNKNOWN"})
        assert result["healthy"] is False

    def test_health_check_records_log(self, logger):
        logger.health_check({"state": "RUNNING", "stateReason": ""})
        logs = logger.get_logs()
        assert len(logs) == 1
        assert logs[0].event == "health_check"


class TestLogRetrieval:
    def test_get_logs_returns_all(self, logger):
        rid1 = logger.start("a")
        logger.end(rid1, "success")
        rid2 = logger.start("b")
        logger.end(rid2, "error", error="oops")
        assert len(logger.get_logs()) == 4

    def test_get_logs_for_request_filters(self, logger):
        rid1 = logger.start("a")
        logger.end(rid1, "success")
        rid2 = logger.start("b")
        logger.end(rid2, "error", error="oops")
        filtered = logger.get_logs_for_request(rid1)
        assert len(filtered) == 2
        assert all(e.request_id == rid1 for e in filtered)

    def test_get_logs_for_unknown_request(self, logger):
        logger.start("a")
        assert logger.get_logs_for_request("nonexistent") == []
