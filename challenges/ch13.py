"""
Challenge: Add comprehensive logging to sandbox executions.

Implement a structured logging system for sandbox code executions that
produces JSON log lines suitable for CloudWatch Logs and supports
request-level tracing with timing.
"""

import json
from dataclasses import dataclass, field


@dataclass
class LogEntry:
    """A single structured log entry."""

    timestamp: str
    event: str
    request_id: str
    data: dict = field(default_factory=dict)

    def to_json(self) -> str:
        """Serialize to a single JSON line (CloudWatch Logs format)."""
        obj = {
            "timestamp": self.timestamp,
            "event": self.event,
            "request_id": self.request_id,
            **self.data,
        }
        return json.dumps(obj)


class ExecutionLogger:
    """Structured logger that captures execution lifecycle events.

    Must support:
      - start(code, timeout_seconds) -> request_id
            Records an "execution.start" event with code_length and
            timeout_seconds in data. Returns the generated request_id.
      - end(request_id, status, error=None)
            Records an "execution.end" event with status, duration_ms
            (milliseconds since matching start() call), and error (if any)
            in data.
      - health_check(microvm_state: dict) -> dict
            Records a "health_check" event. Returns a dict with keys:
            "healthy" (bool), "state", "stateReason", "action".
            Healthy states: RUNNING, SUSPENDED. All others need attention.
      - get_logs() -> list[LogEntry]
            Returns all recorded LogEntry objects in order.
      - get_logs_for_request(request_id) -> list[LogEntry]
            Returns only entries matching the given request_id.
    """

    def __init__(self):
        self._logs: list[LogEntry] = []
        self._start_times: dict[str, float] = {}

    def start(self, code: str, timeout_seconds: float = 5.0) -> str:
        """Record execution start. Return the request_id."""
        raise NotImplementedError("Implement ExecutionLogger.start()")

    def end(self, request_id: str, status: str, error: str = None) -> None:
        """Record execution end with duration calculation."""
        raise NotImplementedError("Implement ExecutionLogger.end()")

    def health_check(self, microvm_state: dict) -> dict:
        """Record health check and return health status dict."""
        raise NotImplementedError("Implement ExecutionLogger.health_check()")

    def get_logs(self) -> list[LogEntry]:
        """Return all log entries."""
        raise NotImplementedError("Implement ExecutionLogger.get_logs()")

    def get_logs_for_request(self, request_id: str) -> list[LogEntry]:
        """Return log entries for a specific request_id."""
        raise NotImplementedError("Implement ExecutionLogger.get_logs_for_request()")
