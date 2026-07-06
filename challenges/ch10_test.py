"""Tests for Chapter 10 challenge: resource limits and quotas."""

import pytest
from ch10 import evaluate_request, ExecutionRequest, ResourcePolicy, PolicyDecision


class TestEvaluateRequest:
    def test_allowed_normal_request(self):
        req = ExecutionRequest(code='print("hi")', timeout_seconds=5.0)
        policy = ResourcePolicy()
        result = evaluate_request(req, policy)
        assert result.allowed is True
        assert result.adjusted_timeout is None
        assert result.adjusted_memory is None

    def test_blocked_fork_bomb(self):
        req = ExecutionRequest(code='import os; os.fork()', timeout_seconds=5.0)
        policy = ResourcePolicy()
        result = evaluate_request(req, policy)
        assert result.allowed is False
        assert "os.fork" in result.reason

    def test_blocked_bash_fork_bomb(self):
        req = ExecutionRequest(code=':(){ :|:& };:', timeout_seconds=5.0)
        policy = ResourcePolicy()
        result = evaluate_request(req, policy)
        assert result.allowed is False

    def test_code_too_large(self):
        req = ExecutionRequest(code="x" * 200_000, timeout_seconds=5.0)
        policy = ResourcePolicy(max_code_size_bytes=100_000)
        result = evaluate_request(req, policy)
        assert result.allowed is False
        assert "size" in result.reason.lower()

    def test_timeout_clamped_high(self):
        req = ExecutionRequest(code='print("hi")', timeout_seconds=60.0)
        policy = ResourcePolicy(max_timeout_seconds=30.0)
        result = evaluate_request(req, policy)
        assert result.allowed is True
        assert result.adjusted_timeout == 30.0

    def test_timeout_clamped_low(self):
        req = ExecutionRequest(code='print("hi")', timeout_seconds=0.1)
        policy = ResourcePolicy(min_timeout_seconds=1.0)
        result = evaluate_request(req, policy)
        assert result.allowed is True
        assert result.adjusted_timeout == 1.0

    def test_memory_clamped_high(self):
        req = ExecutionRequest(code='print("hi")', timeout_seconds=5.0, memory_mb=1024)
        policy = ResourcePolicy(max_memory_mb=512)
        result = evaluate_request(req, policy)
        assert result.allowed is True
        assert result.adjusted_memory == 512

    def test_memory_clamped_low(self):
        req = ExecutionRequest(code='print("hi")', timeout_seconds=5.0, memory_mb=32)
        policy = ResourcePolicy(min_memory_mb=64)
        result = evaluate_request(req, policy)
        assert result.allowed is True
        assert result.adjusted_memory == 64

    def test_custom_blocked_patterns(self):
        req = ExecutionRequest(code='eval("bad")', timeout_seconds=5.0)
        policy = ResourcePolicy(blocked_patterns=["eval("])
        result = evaluate_request(req, policy)
        assert result.allowed is False

    def test_result_is_dataclass(self):
        req = ExecutionRequest(code='print("hi")', timeout_seconds=5.0)
        result = evaluate_request(req, ResourcePolicy())
        assert isinstance(result, PolicyDecision)

    def test_no_adjustments_when_within_bounds(self):
        req = ExecutionRequest(code='print("hi")', timeout_seconds=15.0, memory_mb=256)
        policy = ResourcePolicy()
        result = evaluate_request(req, policy)
        assert result.adjusted_timeout is None
        assert result.adjusted_memory is None
