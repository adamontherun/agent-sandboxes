"""
Central AWS configuration for the runnable examples.

The examples that actually call AWS (Chapters 4-6) need a handful of
account-specific values: your account ID, region, image ARN, and IAM role
ARNs. Rather than editing each script, set them once:

1. Copy ``.env.example`` (in the repo root) to ``.env`` and fill in your
   values.
2. Make sure your AWS credentials are available. Either run ``aws configure``
   once, or put ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` straight
   into the same ``.env`` file.

Every value falls back to an environment variable, so you can also just
export them in your shell or CI instead of using a ``.env`` file. The
``.env`` loader below intentionally has no third-party dependency, so the
examples run with nothing installed beyond this course's own requirements.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root is one level up from this examples/ directory.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_dotenv() -> None:
    """Load KEY=VALUE lines from a repo-root .env into the environment.

    Existing environment variables always win, so an explicit ``export`` or a
    CI-provided secret is never overridden by the file.
    """
    if not _ENV_PATH.exists():
        return
    for raw in _ENV_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

# Non-required values: sensible defaults so display-only examples still run.
REGION = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
ACCOUNT_ID = os.environ.get("AWS_ACCOUNT_ID", "123456789012")


def _require(env_name: str) -> str:
    """Return the value of ``env_name`` or exit with setup instructions."""
    value = os.environ.get(env_name, "")
    if not value:
        raise SystemExit(
            f"Missing required setting {env_name}.\n"
            f"Copy .env.example to .env and fill it in (see the README's "
            f"'Following along with AWS' section), or export {env_name} in "
            f"your environment before running this example."
        )
    return value


def image_arn() -> str:
    """ARN of the MicroVM image to launch (see Chapter 4)."""
    return _require("MICROVM_IMAGE_ARN")


def execution_role_arn() -> str:
    """IAM role a MicroVM assumes at runtime."""
    return _require("MICROVM_EXECUTION_ROLE_ARN")


def build_role_arn() -> str:
    """IAM role used to build MicroVM images."""
    return _require("MICROVM_BUILD_ROLE_ARN")
