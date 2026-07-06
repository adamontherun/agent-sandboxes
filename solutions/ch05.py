"""
Solution: Construct and Parse Lambda MicroVM Lifecycle Requests
"""

from datetime import datetime, timezone


def build_run_microvm_params(image_arn: str, execution_role_arn: str,
                             max_idle_seconds: int = 300,
                             suspended_duration_seconds: int = 300,
                             auto_resume: bool = True) -> dict:
    if not 1 <= max_idle_seconds <= 28800:
        raise ValueError(f"max_idle_seconds must be 1-28800, got {max_idle_seconds}")
    if not 1 <= suspended_duration_seconds <= 28800:
        raise ValueError(f"suspended_duration_seconds must be 1-28800, got {suspended_duration_seconds}")

    return {
        "imageIdentifier": image_arn,
        "executionRoleArn": execution_role_arn,
        "idlePolicy": {
            "maxIdleDurationSeconds": max_idle_seconds,
            "suspendedDurationSeconds": suspended_duration_seconds,
            "autoResumeEnabled": auto_resume,
        },
    }


def build_auth_token_params(microvm_id: str, expiration_minutes: int = 15,
                            allowed_ports: list | None = None) -> dict:
    if not 1 <= expiration_minutes <= 60:
        raise ValueError(f"expiration_minutes must be 1-60, got {expiration_minutes}")

    if allowed_ports is None:
        allowed_ports = [{"allPorts": True}]

    valid_keys = {"port", "range", "allPorts"}
    for spec in allowed_ports:
        if not isinstance(spec, dict):
            raise ValueError(f"Each port spec must be a dict, got {type(spec)}")
        keys = set(spec.keys())
        if len(keys) != 1:
            raise ValueError(f"Port spec is a tagged union: exactly one key required, got {keys}")
        key = next(iter(keys))
        if key not in valid_keys:
            raise ValueError(f"Unknown port spec key '{key}', must be one of: port, range, allPorts")

    return {
        "microvmIdentifier": microvm_id,
        "expirationInMinutes": expiration_minutes,
        "allowedPorts": allowed_ports,
    }


def parse_microvm_status(response: dict) -> dict:
    state = response.get("state", "UNKNOWN")
    endpoint = response.get("endpoint") if state in ("RUNNING", "PENDING", "SUSPENDED") else None

    uptime_seconds = None
    if state == "RUNNING" and "startedAt" in response:
        started = datetime.fromisoformat(response["startedAt"])
        uptime_seconds = (datetime.now(timezone.utc) - started.astimezone(timezone.utc)).total_seconds()

    return {
        "id": response["microvmId"],
        "state": state,
        "endpoint": endpoint,
        "uptime_seconds": uptime_seconds,
        "image_version": response.get("imageVersion", "unknown"),
    }
