"""
Challenge: Dependency resolution for MicroVM package management.

Implement resolve_dependencies() and parse_requirements() below.
"""

from dataclasses import dataclass, field


@dataclass
class DependencyPlan:
    already_available: list[str] = field(default_factory=list)
    needs_install: list[str] = field(default_factory=list)
    install_command: str = ""


def parse_requirements(requirements_text: str) -> list[str]:
    """Parse a requirements.txt-format string into normalized package names."""
    raise NotImplementedError


def resolve_dependencies(requested: list[str], baked: set[str]) -> DependencyPlan:
    """Split requested packages into already-baked vs. needs-install groups."""
    raise NotImplementedError
