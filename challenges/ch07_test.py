"""Tests for Chapter 7 challenge: building a Python code executor."""

from ch07 import ExecutionResult, build_command, is_successful, summarize_result, validate_request


class TestValidateRequest:
    def test_valid_minimal(self):
        assert validate_request({"code": "print(1)"}) is None

    def test_valid_with_timeout(self):
        assert validate_request({"code": "print(1)", "timeout_seconds": 3}) is None

    def test_missing_code(self):
        assert validate_request({}) is not None

    def test_empty_code(self):
        assert validate_request({"code": ""}) is not None

    def test_code_not_a_string(self):
        assert validate_request({"code": 123}) is not None

    def test_negative_timeout(self):
        assert validate_request({"code": "print(1)", "timeout_seconds": -1}) is not None

    def test_zero_timeout(self):
        assert validate_request({"code": "print(1)", "timeout_seconds": 0}) is not None

    def test_non_numeric_timeout(self):
        assert validate_request({"code": "print(1)", "timeout_seconds": "soon"}) is not None


class TestBuildCommand:
    def test_uses_python3(self):
        assert build_command("/tmp/snippet.py") == ["python3", "/tmp/snippet.py"]

    def test_preserves_path(self):
        cmd = build_command("/var/task/abc123.py")
        assert cmd[-1] == "/var/task/abc123.py"

    def test_returns_two_elements(self):
        assert len(build_command("/x.py")) == 2


class TestSummarizeResult:
    def test_success_case(self):
        result = summarize_result("hello\n", "", 0, False)
        assert result == ExecutionResult(stdout="hello\n", stderr="", exit_code=0, timed_out=False)

    def test_failure_case(self):
        result = summarize_result("", "Traceback...\n", 1, False)
        assert result == ExecutionResult(
            stdout="", stderr="Traceback...\n", exit_code=1, timed_out=False
        )

    def test_timeout_case(self):
        result = summarize_result("partial", "[timed out]", None, True)
        assert result == ExecutionResult(
            stdout="partial", stderr="[timed out]", exit_code=None, timed_out=True
        )


class TestIsSuccessful:
    def test_exit_zero_is_successful(self):
        result = ExecutionResult(stdout="ok", stderr="", exit_code=0, timed_out=False)
        assert is_successful(result) is True

    def test_nonzero_exit_is_not_successful(self):
        result = ExecutionResult(stdout="", stderr="err", exit_code=1, timed_out=False)
        assert is_successful(result) is False

    def test_timeout_is_not_successful_even_with_zero_exit(self):
        result = ExecutionResult(stdout="", stderr="", exit_code=0, timed_out=True)
        assert is_successful(result) is False

    def test_none_exit_code_is_not_successful(self):
        result = ExecutionResult(stdout="", stderr="", exit_code=None, timed_out=False)
        assert is_successful(result) is False
