"""Tests for Chapter 9 challenge: file system isolation."""

import os

import pytest
from ch09 import CleanupResult, cleanup_workspace, safe_resolve


class TestSafeResolve:
    def test_simple_filename(self, tmp_path):
        root = str(tmp_path)
        result = safe_resolve(root, "test.py")
        assert result == os.path.join(os.path.realpath(root), "test.py")

    def test_nested_path(self, tmp_path):
        root = str(tmp_path)
        result = safe_resolve(root, "subdir/test.py")
        assert result.endswith(os.path.join("subdir", "test.py"))
        assert result.startswith(os.path.realpath(root))

    def test_traversal_rejected(self, tmp_path):
        root = str(tmp_path)
        with pytest.raises(ValueError, match="traversal"):
            safe_resolve(root, "../etc/passwd")

    def test_double_traversal_rejected(self, tmp_path):
        root = str(tmp_path)
        with pytest.raises(ValueError, match="traversal"):
            safe_resolve(root, "subdir/../../etc/passwd")

    def test_absolute_path_rejected(self, tmp_path):
        root = str(tmp_path)
        with pytest.raises(ValueError):
            safe_resolve(root, "/etc/passwd")

    def test_empty_user_path_rejected(self, tmp_path):
        root = str(tmp_path)
        with pytest.raises(ValueError):
            safe_resolve(root, "")

    def test_relative_root_rejected(self):
        with pytest.raises(ValueError):
            safe_resolve("relative/path", "test.py")

    def test_dot_dot_in_middle(self, tmp_path):
        root = str(tmp_path)
        result = safe_resolve(root, "subdir/../file.py")
        assert result == os.path.join(os.path.realpath(root), "file.py")


class TestCleanupWorkspace:
    def test_removes_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("hello")
        (tmp_path / "b.txt").write_text("world")
        result = cleanup_workspace(str(tmp_path))
        assert set(result.removed) == {"a.txt", "b.txt"}
        assert result.preserved == []
        assert not list(tmp_path.iterdir())

    def test_preserves_specified(self, tmp_path):
        (tmp_path / "keep.txt").write_text("important")
        (tmp_path / "delete.txt").write_text("junk")
        result = cleanup_workspace(str(tmp_path), preserve={"keep.txt"})
        assert "delete.txt" in result.removed
        assert "keep.txt" in result.preserved
        assert (tmp_path / "keep.txt").exists()
        assert not (tmp_path / "delete.txt").exists()

    def test_removes_directories(self, tmp_path):
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("data")
        result = cleanup_workspace(str(tmp_path))
        assert "subdir" in result.removed
        assert not subdir.exists()

    def test_bytes_freed_calculation(self, tmp_path):
        (tmp_path / "file.txt").write_text("x" * 100)
        result = cleanup_workspace(str(tmp_path))
        assert result.bytes_freed == 100

    def test_empty_workspace(self, tmp_path):
        result = cleanup_workspace(str(tmp_path))
        assert result.removed == []
        assert result.bytes_freed == 0

    def test_nonexistent_workspace_raises(self):
        with pytest.raises(ValueError):
            cleanup_workspace("/nonexistent/path/xyz")

    def test_result_is_dataclass(self, tmp_path):
        result = cleanup_workspace(str(tmp_path))
        assert isinstance(result, CleanupResult)
