"""
Challenge: build a malware analysis pipeline.

Implement an AnalysisPipeline that: runs a sample function inside an isolated
context with a network policy that blocks and records outbound connection
attempts, captures what files the sample created, preserves evidence with an
integrity hash, and guarantees a teardown callback always fires — even if the
sample raises an exception.

This models the same pattern as examples/ch16_malware_analysis_pipeline.py
(the full end-to-end demo), distilled into a testable class with no real
filesystem or network — everything is modeled as in-memory function calls.
"""

from dataclasses import dataclass, field


@dataclass
class NetworkAttempt:
    """A recorded outbound network attempt."""

    destination: str
    blocked: bool = True


class NetworkPolicy:
    """Blocks all outbound connections and records attempts.

    Must support:
      - attempt_connection(destination: str) -> bool
            Records the attempt (as a NetworkAttempt with blocked=True) in
            self.attempts, then returns False (blocked).
    """

    def __init__(self) -> None:
        self.attempts: list[NetworkAttempt] = []

    def attempt_connection(self, destination: str) -> bool:
        raise NotImplementedError("Implement NetworkPolicy.attempt_connection()")


@dataclass
class Evidence:
    """Preserved evidence from an analysis run.

    Fields:
      - sample_id: str — identifier for this analysis run
      - files_created: list[str] — files the sample wrote
      - network_attempts: list[NetworkAttempt] — blocked connection attempts
      - artifact_hash: str — SHA-256 hex digest of all artifact contents
        concatenated in sorted order (sorted by filename)
      - teardown_called: bool — whether teardown completed
    """

    sample_id: str
    files_created: list[str] = field(default_factory=list)
    network_attempts: list[NetworkAttempt] = field(default_factory=list)
    artifact_hash: str = ""
    teardown_called: bool = False


class AnalysisPipeline:
    """Runs a sample in isolation, captures behavior, preserves evidence,
    and guarantees teardown.

    Must support:
      - __init__(sample_id: str, teardown_callback: callable)
            Stores sample_id and teardown_callback. Initializes:
              - self.network = NetworkPolicy()
              - self.files: dict[str, bytes] = {}  (filename -> content)
              - self._torn_down: bool = False
      - write_file(name: str, content: bytes) -> None
            Records content under name in self.files.
      - run(sample_fn: callable) -> Evidence
            Executes sample_fn(self) inside a try/finally that guarantees
            teardown. sample_fn receives this pipeline instance and may call
            self.write_file() and self.network.attempt_connection().
            After sample_fn completes (or raises), the finally block must:
              1. Call self.teardown_callback() (always, even on exception).
              2. Set self._torn_down = True.
            If sample_fn raises, re-raise the exception AFTER teardown.
            Before returning (on success), build and return an Evidence:
              - sample_id from self
              - files_created = sorted(self.files.keys())
              - network_attempts = list(self.network.attempts)
              - artifact_hash = SHA-256 hex digest of the concatenation of
                self.files[name] for each name in sorted(self.files.keys()).
                If no files, artifact_hash is the SHA-256 of b"" (empty bytes).
              - teardown_called = self._torn_down
      - compute_hash() -> str
            Returns the SHA-256 hex digest described above (same logic as
            run() uses for artifact_hash), available as a standalone method.
    """

    def __init__(self, sample_id: str, teardown_callback):
        raise NotImplementedError("Implement AnalysisPipeline.__init__()")

    def write_file(self, name: str, content: bytes) -> None:
        raise NotImplementedError("Implement AnalysisPipeline.write_file()")

    def run(self, sample_fn) -> Evidence:
        raise NotImplementedError("Implement AnalysisPipeline.run()")

    def compute_hash(self) -> str:
        raise NotImplementedError("Implement AnalysisPipeline.compute_hash()")
