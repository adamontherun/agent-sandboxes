"""Tests for Chapter 5 challenge: RunMicrovm params, auth token params, status parsing"""

import pytest
from ch05 import build_auth_token_params, build_run_microvm_params, parse_microvm_status


class TestBuildRunMicrovmParams:
    def test_basic_params(self):
        result = build_run_microvm_params(
            "arn:aws:lambda:us-east-1:123456789012:microvm-image:my-image",
            "arn:aws:iam::123456789012:role/MyRole",
        )
        assert (
            result["imageIdentifier"]
            == "arn:aws:lambda:us-east-1:123456789012:microvm-image:my-image"
        )
        assert result["executionRoleArn"] == "arn:aws:iam::123456789012:role/MyRole"

    def test_idle_policy_all_three_fields(self):
        result = build_run_microvm_params(
            "arn:aws:lambda:us-east-1:123456789012:microvm-image:my-image",
            "arn:aws:iam::123456789012:role/MyRole",
            max_idle_seconds=600,
            suspended_duration_seconds=1800,
            auto_resume=False,
        )
        policy = result["idlePolicy"]
        assert policy["maxIdleDurationSeconds"] == 600
        assert policy["suspendedDurationSeconds"] == 1800
        assert policy["autoResumeEnabled"] is False

    def test_idle_policy_always_has_all_fields(self):
        """All three idle policy fields must always be present together."""
        result = build_run_microvm_params(
            "arn:aws:lambda:us-east-1:123456789012:microvm-image:my-image",
            "arn:aws:iam::123456789012:role/MyRole",
        )
        policy = result["idlePolicy"]
        assert "maxIdleDurationSeconds" in policy
        assert "suspendedDurationSeconds" in policy
        assert "autoResumeEnabled" in policy

    def test_invalid_max_idle_seconds_zero(self):
        with pytest.raises(ValueError):
            build_run_microvm_params(
                "arn:aws:lambda:us-east-1:123456789012:microvm-image:my-image",
                "arn:aws:iam::123456789012:role/MyRole",
                max_idle_seconds=0,
            )

    def test_invalid_max_idle_seconds_too_high(self):
        with pytest.raises(ValueError):
            build_run_microvm_params(
                "arn:aws:lambda:us-east-1:123456789012:microvm-image:my-image",
                "arn:aws:iam::123456789012:role/MyRole",
                max_idle_seconds=30000,
            )

    def test_invalid_suspended_duration_zero(self):
        with pytest.raises(ValueError):
            build_run_microvm_params(
                "arn:aws:lambda:us-east-1:123456789012:microvm-image:my-image",
                "arn:aws:iam::123456789012:role/MyRole",
                suspended_duration_seconds=0,
            )


class TestBuildAuthTokenParams:
    def test_basic_params(self):
        result = build_auth_token_params("microvm-abc123")
        assert result["microvmIdentifier"] == "microvm-abc123"
        assert result["expirationInMinutes"] == 15

    def test_default_all_ports(self):
        result = build_auth_token_params("microvm-abc123")
        assert result["allowedPorts"] == [{"allPorts": True}]

    def test_specific_port(self):
        result = build_auth_token_params("microvm-abc123", allowed_ports=[{"port": 5000}])
        assert result["allowedPorts"] == [{"port": 5000}]

    def test_port_range(self):
        result = build_auth_token_params(
            "microvm-abc123", allowed_ports=[{"range": {"start": 8000, "end": 9000}}]
        )
        assert result["allowedPorts"] == [{"range": {"start": 8000, "end": 9000}}]

    def test_invalid_port_spec_multiple_keys(self):
        """Each port spec is a tagged union - only one key allowed."""
        with pytest.raises(ValueError):
            build_auth_token_params(
                "microvm-abc123", allowed_ports=[{"port": 5000, "allPorts": True}]
            )

    def test_invalid_port_spec_unknown_key(self):
        with pytest.raises(ValueError):
            build_auth_token_params("microvm-abc123", allowed_ports=[{"protocol": "HTTP"}])

    def test_invalid_expiration_too_high(self):
        with pytest.raises(ValueError):
            build_auth_token_params("microvm-abc123", expiration_minutes=120)

    def test_invalid_expiration_zero(self):
        with pytest.raises(ValueError):
            build_auth_token_params("microvm-abc123", expiration_minutes=0)


class TestParseMicrovmStatus:
    def test_running_microvm(self):
        response = {
            "microvmId": "microvm-29fabacb-68fe-30ed-b477-39bf36e55b16",
            "state": "RUNNING",
            "endpoint": "abc123.lambda-microvm.us-east-1.on.aws",
            "imageVersion": "11.0",
            "startedAt": "2026-07-05T21:43:41.138000-10:00",
        }
        result = parse_microvm_status(response)
        assert result["id"] == "microvm-29fabacb-68fe-30ed-b477-39bf36e55b16"
        assert result["state"] == "RUNNING"
        assert result["endpoint"] == "abc123.lambda-microvm.us-east-1.on.aws"
        assert result["image_version"] == "11.0"

    def test_terminated_microvm(self):
        response = {
            "microvmId": "microvm-terminated-123",
            "state": "TERMINATED",
            "imageVersion": "3.0",
            "startedAt": "2026-07-05T20:00:00.000000-10:00",
        }
        result = parse_microvm_status(response)
        assert result["id"] == "microvm-terminated-123"
        assert result["state"] == "TERMINATED"
        assert result["endpoint"] is None

    def test_pending_microvm(self):
        response = {
            "microvmId": "microvm-pending-456",
            "state": "PENDING",
            "endpoint": "xyz789.lambda-microvm.us-east-1.on.aws",
            "imageVersion": "1.0",
            "startedAt": "2026-07-05T22:00:00.000000-10:00",
        }
        result = parse_microvm_status(response)
        assert result["state"] == "PENDING"
        assert result["uptime_seconds"] is None
