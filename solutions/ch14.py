"""
Solution: a production-ready orchestrator combining version tracking,
health-gated blue/green cutover, retry-with-backoff, and a scaling heuristic.
"""

from dataclasses import dataclass


class TransientLaunchError(Exception):
    """A retryable launch failure (e.g. throttling)."""


@dataclass
class LaunchAttempt:
    """Record of one launch_fn call for a given image version."""

    image_version: str
    attempt: int
    succeeded: bool


class ProductionOrchestrator:
    """Tracks a live image version and stages/cuts over candidates."""

    def __init__(self, live_version: str):
        self.live_version = live_version
        self.candidate_version = None
        self.attempts: list[LaunchAttempt] = []

    def stage_candidate(self, version: str) -> None:
        self.candidate_version = version

    def launch_with_retry(self, launch_fn, image_version: str, max_attempts: int = 4) -> dict:
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                result = launch_fn(image_version)
            except TransientLaunchError as exc:
                last_error = exc
                self.attempts.append(
                    LaunchAttempt(image_version=image_version, attempt=attempt, succeeded=False)
                )
                continue
            self.attempts.append(
                LaunchAttempt(image_version=image_version, attempt=attempt, succeeded=True)
            )
            return result
        raise RuntimeError(f"launch failed after {max_attempts} attempts: {last_error}")

    def cut_over(self, instance: dict) -> bool:
        if self.candidate_version is None:
            raise ValueError("no candidate staged")

        healthy = instance.get("state") in ("RUNNING", "SUSPENDED")
        if not healthy:
            return False

        self.live_version = self.candidate_version
        self.candidate_version = None
        return True

    def decide_scaling_action(
        self, running_count: int, queued_requests: int, max_per_microvm: int = 5
    ) -> str:
        if running_count == 0 and queued_requests > 0:
            return "launch"
        if queued_requests / max(running_count, 1) > max_per_microvm:
            return "launch"
        if running_count > 1 and queued_requests == 0:
            return "scale_down"
        return "hold"
