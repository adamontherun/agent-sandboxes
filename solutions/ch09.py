"""
Solution: File system isolation — safe path resolution and workspace cleanup.
"""

import contextlib
import os
import shutil
from dataclasses import dataclass, field


@dataclass
class CleanupResult:
    """Result of cleaning a workspace directory."""

    removed: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    bytes_freed: int = 0


def safe_resolve(root: str, user_path: str) -> str:
    """
    Safely resolve a user-supplied path within a sandboxed root directory.

    Prevents path traversal attacks by ensuring the resolved path is always
    within the root directory.
    """
    if not root or not os.path.isabs(root):
        raise ValueError(f"Root must be an absolute path, got: {root!r}")

    if not user_path:
        raise ValueError("User path must not be empty")

    if os.path.isabs(user_path):
        raise ValueError(f"User path must be relative, got absolute: {user_path!r}")

    root_resolved = os.path.realpath(root)
    target = os.path.realpath(os.path.join(root_resolved, user_path))

    if not target.startswith(root_resolved + os.sep) and target != root_resolved:
        raise ValueError(f"Path traversal detected: {user_path!r} resolves outside root")

    return target


def cleanup_workspace(workspace_dir: str, preserve: set[str] | None = None) -> CleanupResult:
    """
    Remove all files and directories in workspace_dir except preserved entries.
    """
    if not os.path.isdir(workspace_dir):
        raise ValueError(f"Workspace directory does not exist: {workspace_dir!r}")

    preserve = preserve or set()
    result = CleanupResult()

    for entry in os.listdir(workspace_dir):
        entry_path = os.path.join(workspace_dir, entry)
        if entry in preserve:
            result.preserved.append(entry)
            continue

        if os.path.isfile(entry_path) or os.path.islink(entry_path):
            result.bytes_freed += os.path.getsize(entry_path)
            os.unlink(entry_path)
        elif os.path.isdir(entry_path):
            for dirpath, _dirnames, filenames in os.walk(entry_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    with contextlib.suppress(OSError):
                        result.bytes_freed += os.path.getsize(fp)
            shutil.rmtree(entry_path)

        result.removed.append(entry)

    return result
