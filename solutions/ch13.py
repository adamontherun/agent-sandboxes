"""
Solution: comprehensive structured logging for sandbox executions.
"""

import json
import time
import uuid
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
    """Structured logger that captures execution lifecycle events."""

    def __init__(self):
        self._logs: list[LogEntry] = []
        self._start_times: dict[str, float] = {}

    def _now(self) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _record(self, event: str, request_id: str, **data) -> LogEntry:
        entry = LogEntry(
            timestamp=self._now(),
            event=event,
            request_id=request_id,
            data=data,
        )
        self._logs.append(entry)
        return entry

    def start(self, code: str, timeout_seconds: float = 5.0) -> str:
        """Record execution start. Return the request_id."""
        request_id = str(uuid.uuid4())
        self._start_times[request_id] = time.perf_counter()
        self._record(
            "execution.start",
            request_id,
            code_length=len(code),
            timeout_seconds=timeout_seconds,
        )
        return request_id

    def end(self, request_id: str, status: str, error: str = None) -> None:
        """Record execution end with duration calculation."""
        start_time = self._start_times.get(request_id)
        duration_ms = 0.0
        if start_time is not None:
            duration_ms = (time.perf_counter() - start_time) * 1000

        self._record(
            "execution.end",
            request_id,
            status=status,
            duration_ms=round(duration_ms, 2),
            error=error,
        )

    def health_check(self, microvm_state: dict) -> dict:
        """Record health check and return health status dict."""
        state = microvm_state.get("state", "UNKNOWN")
        state_reason = microvm_state.get("stateReason", "")

        healthy = state in ("RUNNING", "SUSPENDED")

        result = {
            "healthy": healthy,
            "state": state,
            "stateReason": state_reason,
            "action": "none" if healthy else "investigate",
        }

        request_id = str(uuid.uuid4())
        self._record(
            "health_check",
            request_id,
            microvm_state=state,
            healthy=healthy,
            state_reason=state_reason,
        )

        return result

    def get_logs(self) -> list[LogEntry]:
        """Return all log entries."""
        return list(self._logs)

    def get_logs_for_request(self, request_id: str) -> list[LogEntry]:
        """Return log entries for a specific request_id."""
        return [e for e in self._logs if e.request_id == request_id]
