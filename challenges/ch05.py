"""
Challenge: Construct and Parse Lambda MicroVM Lifecycle Requests

Implement functions for building RunMicrovm request parameters and
parsing GetMicrovm response data — the kind of helper code you'd write
in a real SDK wrapper around the Lambda MicroVMs API.
"""


def build_run_microvm_params(image_arn: str, execution_role_arn: str,
                             max_idle_seconds: int = 300,
                             suspended_duration_seconds: int = 300,
                             auto_resume: bool = True) -> dict:
    """
    Build the parameters dictionary for a RunMicrovm API call.

    The idle policy is tricky: all three fields (maxIdleDurationSeconds,
    suspendedDurationSeconds, autoResumeEnabled) are REQUIRED together.
    This function ensures they are always included as a unit.

    Args:
        image_arn: Full ARN of the MicroVM image to launch.
        execution_role_arn: IAM role ARN for the MicroVM to assume.
        max_idle_seconds: Seconds of inactivity before auto-suspend (1-28800).
        suspended_duration_seconds: Seconds to remain suspended before termination (1-28800).
        auto_resume: Whether to auto-resume on incoming request.

    Returns:
        A dictionary matching the RunMicrovm API parameter shape, with keys:
        "imageIdentifier", "executionRoleArn", "idlePolicy".

    Raises:
        ValueError: If any parameter is out of valid range.
    """
    raise NotImplementedError


def build_auth_token_params(microvm_id: str, expiration_minutes: int = 15,
                            allowed_ports: list | None = None) -> dict:
    """
    Build parameters for a CreateMicrovmAuthToken API call.

    Each entry in allowed_ports must be a tagged union with exactly ONE of:
    - {"port": int}
    - {"range": {"start": int, "end": int}}
    - {"allPorts": True}

    Args:
        microvm_id: The MicroVM identifier.
        expiration_minutes: Token validity in minutes (1-60).
        allowed_ports: List of port specifications. Defaults to [{"allPorts": True}].

    Returns:
        A dictionary matching the CreateMicrovmAuthToken API parameter shape.

    Raises:
        ValueError: If any port spec has invalid structure or expiration is out of range.
    """
    raise NotImplementedError


def parse_microvm_status(response: dict) -> dict:
    """
    Parse a GetMicrovm response into a simplified status summary.

    Args:
        response: The raw GetMicrovm API response dictionary.

    Returns:
        A dict with keys:
        - "id" (str): The microvmId
        - "state" (str): Current state (PENDING, RUNNING, SUSPENDED, TERMINATED)
        - "endpoint" (str or None): The endpoint URL if available
        - "uptime_seconds" (float or None): Seconds since startedAt, if running
        - "image_version" (str): The image version in use
    """
    raise NotImplementedError
