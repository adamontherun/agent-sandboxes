"""
Runnable example: demonstrate safe_resolve and cleanup_workspace.

Simulates a MicroVM workspace directory. Shows:
  1. Safely resolving user-supplied paths inside the sandbox root.
  2. Rejecting path traversal attempts.
  3. Cleaning up between executions while preserving pinned files.

Run:
    python3 examples/ch09_filesystem_isolation.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solutions"))

from ch09 import cleanup_workspace, safe_resolve


def demo_safe_resolve(root: str) -> None:
    print("=== safe_resolve ===")

    ok_cases = ["input.txt", "data/nested/file.json", "subdir/../top.py"]
    for p in ok_cases:
        resolved = safe_resolve(root, p)
        print(f"  OK    {p!r:40s} -> {resolved}")

    bad_cases = ["../etc/passwd", "/etc/passwd", "a/../../../../etc/passwd"]
    for p in bad_cases:
        try:
            safe_resolve(root, p)
            print(f"  MISS  {p!r} was NOT rejected (bug!)")
        except ValueError as e:
            print(f"  BLOCK {p!r:40s} -> {e}")


def demo_cleanup(root: str) -> None:
    print("\n=== cleanup_workspace ===")

    for name, content in [
        ("scratch.py", "print('hi')\n"),
        ("output.log", "x" * 2048),
        ("cache.bin", "y" * 4096),
    ]:
        with open(os.path.join(root, name), "w") as f:
            f.write(content)

    subdir = os.path.join(root, "artifacts")
    os.makedirs(subdir, exist_ok=True)
    with open(os.path.join(subdir, "build.tar"), "wb") as f:
        f.write(b"z" * 8192)

    print(f"  before: {sorted(os.listdir(root))}")

    result = cleanup_workspace(root, preserve={"scratch.py"})

    print(f"  removed:      {result.removed}")
    print(f"  preserved:    {result.preserved}")
    print(f"  bytes freed:  {result.bytes_freed}")
    print(f"  after:        {sorted(os.listdir(root))}")


def main() -> None:
    with tempfile.TemporaryDirectory() as workspace:
        print(f"Sandbox root: {workspace}\n")
        demo_safe_resolve(workspace)
        demo_cleanup(workspace)


if __name__ == "__main__":
    main()
