"""
Challenge: Validate CreateMicrovmImage Parameters

Implement a function that validates the parameters for a CreateMicrovmImage
API call. This mimics the kind of pre-flight validation your deployment
tooling should do before sending a request to AWS, catching common mistakes
locally rather than waiting for a remote build to fail.
"""


def validate_create_image_params(params: dict) -> list[str]:
    """
    Validate parameters for a CreateMicrovmImage API call.

    Args:
        params: A dictionary with keys that may include:
            - name (str): Image name (required, 1-64 chars, alphanumeric + hyphens)
            - base_image_arn (str): Base image ARN (required, must match pattern)
            - build_role_arn (str): IAM role ARN (required, must match pattern)
            - code_artifact (dict): Must have exactly one key: "uri" (required)
            - resources (dict, optional): May contain "memoryInMiB" (2048-32768)
              and/or "vcpus" (1-16) and/or "diskInGiB" (1-32)

    Returns:
        A list of error strings. Empty list means params are valid.
    """
    raise NotImplementedError


def generate_dockerfile(base_image: str, app_file: str, packages: list[str],
                        port: int = 5000) -> str:
    """
    Generate a Dockerfile string for a Lambda MicroVM image.

    Args:
        base_image: The base image to use (e.g. "public.ecr.aws/lambda/microvms:al2023-minimal")
        app_file: The application entrypoint filename (e.g. "app.py")
        packages: List of pip packages to install (e.g. ["flask", "requests"])
        port: The port the application listens on (default 5000)

    Returns:
        A string containing a valid Dockerfile.
    """
    raise NotImplementedError
