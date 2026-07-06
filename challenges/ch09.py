"""
Challenge: File system isolation — safe path resolution and workspace cleanup.

Implement `safe_resolve` and `cleanup_workspace` per the spec in the chapter.
"""

from dataclasses import dataclass, field


@dataclass
class CleanupResult:
    """Result of cleaning a workspace directory."""
    removed: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    bytes_freed: int = 0


def safe_resolve(root: str, user_path: str) -> str:
    raise NotImplementedError


def cleanup_workspace(workspace_dir: str, preserve: set[str] | None = None) -> CleanupResult:
    raise NotImplementedError
