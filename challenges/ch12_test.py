"""Tests for Chapter 12 challenge: hardening a sandbox against common attacks."""

import pytest
from ch12 import SandboxHardener, ScanResult


@pytest.fixture
def hardener():
    return SandboxHardener()


class TestSafeCode:
    def test_arithmetic_is_safe(self, hardener):
        result = hardener.scan("result = sum(x * x for x in range(10))\n")
        assert result.safe is True
        assert result.violations == []

    def test_json_usage_is_safe(self, hardener):
        result = hardener.scan("import json\ndata = json.loads('{\"a\": 1}')\n")
        assert result.safe is True

    def test_result_is_dataclass(self, hardener):
        result = hardener.scan("x = 1\n")
        assert isinstance(result, ScanResult)


class TestDangerousImports:
    def test_ctypes_import_blocked(self, hardener):
        result = hardener.scan("import ctypes\n")
        assert result.safe is False
        assert any("ctypes" in v for v in result.violations)

    def test_cffi_import_blocked(self, hardener):
        result = hardener.scan("import cffi\n")
        assert result.safe is False

    def test_ctypes_import_from_blocked(self, hardener):
        result = hardener.scan("from ctypes import CDLL\n")
        assert result.safe is False


class TestDangerousCalls:
    def test_os_system_blocked(self, hardener):
        result = hardener.scan("import os\nos.system('id')\n")
        assert result.safe is False
        assert any("os.system" in v for v in result.violations)

    def test_os_fork_blocked(self, hardener):
        result = hardener.scan("import os\nos.fork()\n")
        assert result.safe is False

    def test_subprocess_run_blocked(self, hardener):
        result = hardener.scan("import subprocess\nsubprocess.run(['ls'])\n")
        assert result.safe is False

    def test_shell_true_blocked_even_on_other_call(self, hardener):
        result = hardener.scan("import subprocess\nsubprocess.run('rm -rf /', shell=True)\n")
        assert result.safe is False
        assert any("shell" in v for v in result.violations)

    def test_socket_socket_blocked(self, hardener):
        result = hardener.scan("import socket\nsocket.socket()\n")
        assert result.safe is False

    def test_eval_blocked(self, hardener):
        result = hardener.scan("eval('1+1')\n")
        assert result.safe is False

    def test_exec_blocked(self, hardener):
        result = hardener.scan("exec('x = 1')\n")
        assert result.safe is False

    def test_dunder_import_blocked(self, hardener):
        result = hardener.scan("__import__('os').system('id')\n")
        assert result.safe is False


class TestSyntaxErrors:
    def test_syntax_error_is_unsafe(self, hardener):
        result = hardener.scan("def broken(:\n")
        assert result.safe is False
        assert result.violations
