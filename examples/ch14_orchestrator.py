"""
Runnable example: a small production orchestrator tying together the
patterns Chapter 14 covers - image-version tracking, a blue/green health-gated
cutover, and retry-with-backoff around a flaky launch call.

No AWS calls required - RunMicrovm and GetMicrovm are simulated locally so
the retry/backoff and cutover logic can run deterministically and offline,
the same "simulate the API shape, not the network" approach Chapter 13's
example used for health checks.
"""

import random
import time


class TransientLaunchError(Exception):
    """Simulates a transient RunMicrovm failure (e.g. throttling)."""


def launch_microvm(image_version: str, attempt_state: dict) -> dict:
    """Simulate RunMicrovm, failing on the first two calls per image version
    to exercise the retry loop below, then succeeding.

    attempt_state tracks how many times this image_version has been tried,
    since a real RunMicrovm call doesn't take a "fail N times" parameter -
    this is purely a test harness for the retry logic, not a claim about
    real API failure rates.
    """
    attempt_state[image_version] = attempt_state.get(image_version, 0) + 1
    if attempt_state[image_version] <= 2:
        raise TransientLaunchError(f"throttled launching image version {image_version}")
    return {
        "microvmId": f"microvm-{image_version}-{attempt_state[image_version]}",
        "state": "RUNNING",
        "imageVersion": image_version,
    }


def launch_with_retry(image_version: str, attempt_state: dict, max_attempts: int = 4) -> dict:
    """Retry a launch with exponential backoff, matching Chapter 6/13's
    guidance to treat transient failures (still-running instance, throttling)
    differently from structural ones (terminated/failed instance).

    Backoff is capped and jittered to avoid a thundering herd if many
    orchestrator workers retry a throttled launch at the same moment.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return launch_microvm(image_version, attempt_state)
        except TransientLaunchError as exc:
            last_error = exc
            if attempt == max_attempts:
                break
            backoff_seconds = min(2 ** (attempt - 1), 8) + random.uniform(0, 0.1)
            print(f"  attempt {attempt} failed ({exc}); retrying in {backoff_seconds:.2f}s")
            time.sleep(0.01)  # kept short for the demo; real backoff_seconds above
    raise RuntimeError(f"launch failed after {max_attempts} attempts: {last_error}")


def check_health(microvm_state: dict) -> bool:
    """Same healthy-state check as Chapter 13's ExecutionLogger.health_check:
    RUNNING and SUSPENDED are healthy, everything else needs attention.
    """
    return microvm_state.get("state") in ("RUNNING", "SUSPENDED")


class BlueGreenOrchestrator:
    """Tracks a "blue" (currently live) and "green" (candidate) image
    version, and only cuts traffic over to green once it launches
    successfully and passes a health check - never a hard swap on a bare
    version bump.
    """

    def __init__(self, blue_version: str):
        self.blue_version = blue_version
        self.green_version = None
        self.live_version = blue_version

    def stage_candidate(self, new_version: str) -> None:
        print(f"Staging candidate image version {new_version} alongside live {self.live_version}")
        self.green_version = new_version

    def cut_over(self, instance: dict) -> bool:
        """Health-check an already-launched green candidate instance, and
        only then flip live traffic to it. Returns whether the cutover
        happened. Takes the launched instance directly (rather than
        launching it itself) so callers can plug in launch_with_retry's
        real result or, for a demo, a synthetic unhealthy one.
        """
        if self.green_version is None:
            raise ValueError("no candidate staged")

        if not check_health(instance):
            print(
                f"Candidate {self.green_version} failed health check "
                f"(state={instance.get('state')}); aborting cutover, staying on {self.live_version}"
            )
            return False

        print(f"Candidate {self.green_version} healthy - cutting traffic over")
        self.blue_version = self.live_version
        self.live_version = self.green_version
        self.green_version = None
        return True


def decide_scaling_action(
    running_count: int, queued_requests: int, max_per_microvm: int = 5
) -> str:
    """A minimal scale-out heuristic: launch another MicroVM once the
    queue backlog per running instance exceeds max_per_microvm. This mirrors
    Chapter 13's framing that ListMicrovms/GetMicrovm state, not a dedicated
    metrics API, is the raw signal Lambda MicroVMs gives you for capacity
    decisions - there's no autoscaling group or target-tracking policy built
    into the service itself.
    """
    if running_count == 0 and queued_requests > 0:
        return "launch"
    if queued_requests / max(running_count, 1) > max_per_microvm:
        return "launch"
    if running_count > 1 and queued_requests == 0:
        return "scale_down"
    return "hold"


if __name__ == "__main__":
    print("=== Retry with backoff ===\n")
    attempt_state: dict = {}
    result = launch_with_retry("14.0", attempt_state)
    print(f"  -> launched {result['microvmId']} on image version {result['imageVersion']}\n")

    print("=== Blue/green cutover: healthy candidate ===\n")
    orchestrator = BlueGreenOrchestrator(blue_version="13.0")
    orchestrator.stage_candidate("14.0")
    healthy_instance = launch_with_retry("14.0", attempt_state={})
    cut = orchestrator.cut_over(healthy_instance)
    print(f"  -> cutover happened={cut}, live_version={orchestrator.live_version}\n")

    print("=== Blue/green cutover: unhealthy candidate stays on blue ===\n")
    orchestrator2 = BlueGreenOrchestrator(blue_version="13.0")
    orchestrator2.stage_candidate("14.1")
    unhealthy_instance = {
        "microvmId": "microvm-14.1-1",
        "state": "TERMINATED",
        "imageVersion": "14.1",
    }
    cut2 = orchestrator2.cut_over(unhealthy_instance)
    print(f"  -> cutover happened={cut2}, live_version={orchestrator2.live_version}\n")

    print("=== Scaling decisions ===\n")
    for running, queued in [(0, 3), (2, 15), (3, 0), (2, 4)]:
        action = decide_scaling_action(running, queued)
        print(f"  running={running}, queued={queued} -> {action}")

    print("\n=== Done ===")
