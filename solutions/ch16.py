"""
Solution: a malware analysis pipeline that runs a sample in isolation,
captures behavior, preserves evidence with an integrity hash, and
guarantees teardown even if the sample raises.
"""

import hashlib
from dataclasses import dataclass, field


@dataclass
class NetworkAttempt:
    """A recorded outbound network attempt."""

    destination: str
    blocked: bool = True


class NetworkPolicy:
    """Blocks all outbound connections and records attempts."""

    def __init__(self) -> None:
        self.attempts: list[NetworkAttempt] = []

    def attempt_connection(self, destination: str) -> bool:
        attempt = NetworkAttempt(destination=destination, blocked=True)
        self.attempts.append(attempt)
        return False


@dataclass
class Evidence:
    """Preserved evidence from an analysis run."""

    sample_id: str
    files_created: list[str] = field(default_factory=list)
    network_attempts: list[NetworkAttempt] = field(default_factory=list)
    artifact_hash: str = ""
    teardown_called: bool = False


class AnalysisPipeline:
    """Runs a sample in isolation, captures behavior, preserves evidence,
    and guarantees teardown."""

    def __init__(self, sample_id: str, teardown_callback):
        self.sample_id = sample_id
        self.teardown_callback = teardown_callback
        self.network = NetworkPolicy()
        self.files: dict[str, bytes] = {}
        self._torn_down: bool = False

    def write_file(self, name: str, content: bytes) -> None:
        self.files[name] = content

    def run(self, sample_fn) -> Evidence:
        try:
            sample_fn(self)
        except BaseException:
            raise
        finally:
            self.teardown_callback()
            self._torn_down = True

        return Evidence(
            sample_id=self.sample_id,
            files_created=sorted(self.files.keys()),
            network_attempts=list(self.network.attempts),
            artifact_hash=self.compute_hash(),
            teardown_called=self._torn_down,
        )

    def compute_hash(self) -> str:
        hasher = hashlib.sha256()
        for name in sorted(self.files.keys()):
            hasher.update(self.files[name])
        return hasher.hexdigest()
