"""
Solution: Dependency resolution for MicroVM package management.
"""

import re
from dataclasses import dataclass, field


@dataclass
class DependencyPlan:
    already_available: list[str] = field(default_factory=list)
    needs_install: list[str] = field(default_factory=list)
    install_command: str = ""


def parse_requirements(requirements_text: str) -> list[str]:
    packages = []
    for line in requirements_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        line = line.split("#")[0].strip()
        line = line.split(";")[0].strip()
        if not line:
            continue
        match = re.match(r'^([A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?)', line)
        if match:
            packages.append(match.group(1).lower())
    return packages


def resolve_dependencies(requested: list[str], baked: set[str]) -> DependencyPlan:
    baked_lower = {p.lower() for p in baked}
    already_available = []
    needs_install = []

    for pkg in requested:
        if pkg.lower() in baked_lower:
            already_available.append(pkg)
        else:
            needs_install.append(pkg)

    install_command = ""
    if needs_install:
        install_command = f"pip install {' '.join(needs_install)}"

    return DependencyPlan(
        already_available=already_available,
        needs_install=needs_install,
        install_command=install_command,
    )
