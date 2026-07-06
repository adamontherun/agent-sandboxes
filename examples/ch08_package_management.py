"""
Runnable example: dependency planning for a MicroVM image.

Given a MicroVM image with some packages already baked in, plan what a
running agent would need to `pip install` at runtime.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "solutions"))

from ch08 import parse_requirements, resolve_dependencies


BAKED_INTO_IMAGE = {"flask", "requests", "boto3", "numpy"}

REQUIREMENTS_TXT = """
# Web layer
flask>=3.0
requests==2.31.0  # pinned for reproducibility

# Data
numpy~=1.26
pandas>=2.0

# Extras
celery[redis]>=5.3
pywin32; sys_platform == 'win32'

-r dev-requirements.txt
"""


def main() -> None:
    print("Baked into MicroVM image:")
    for pkg in sorted(BAKED_INTO_IMAGE):
        print(f"  - {pkg}")

    requested = parse_requirements(REQUIREMENTS_TXT)
    print(f"\nParsed from requirements.txt ({len(requested)}):")
    for pkg in requested:
        print(f"  - {pkg}")

    plan = resolve_dependencies(requested, BAKED_INTO_IMAGE)

    print(f"\nAlready available in image ({len(plan.already_available)}):")
    for pkg in plan.already_available:
        print(f"  - {pkg}")

    print(f"\nNeeds runtime install ({len(plan.needs_install)}):")
    for pkg in plan.needs_install:
        print(f"  - {pkg}")

    print("\nInstall command to run inside MicroVM:")
    print(f"  {plan.install_command or '(nothing to install)'}")


if __name__ == "__main__":
    main()
