"""
Solution: Validate CreateMicrovmImage Parameters
"""

import re


def validate_create_image_params(params: dict) -> list[str]:
    """
    Validate parameters for a CreateMicrovmImage API call.
    """
    errors = []

    # Required fields
    required = ["name", "base_image_arn", "build_role_arn", "code_artifact"]
    for field in required:
        if field not in params:
            errors.append(f"Missing required parameter: {field}")

    # Name validation
    if "name" in params:
        name = params["name"]
        if not isinstance(name, str) or len(name) == 0 or len(name) > 64:
            errors.append("name must be 1-64 characters")
        elif not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\-]*$", name):
            errors.append("name must contain only alphanumeric characters and hyphens")

    # base_image_arn validation
    if "base_image_arn" in params:
        arn = params["base_image_arn"]
        if not re.match(r"^arn:aws:lambda:[a-z0-9\-]+:(aws|\d{12}):microvm-image:", arn):
            errors.append("base_image_arn must be a valid Lambda MicroVM image ARN")

    # build_role_arn validation
    if "build_role_arn" in params:
        arn = params["build_role_arn"]
        if not re.match(r"^arn:aws:iam::\d{12}:role/", arn):
            errors.append("build_role_arn must be a valid IAM role ARN")

    # code_artifact validation (tagged union: exactly one key "uri")
    if "code_artifact" in params:
        ca = params["code_artifact"]
        if not isinstance(ca, dict) or "uri" not in ca:
            errors.append("code_artifact must contain a 'uri' key")
        elif len(ca) > 1:
            errors.append("code_artifact is a tagged union: only 'uri' key is allowed")

    # Optional resources validation
    if "resources" in params:
        res = params["resources"]
        if "memoryInMiB" in res:
            mem = res["memoryInMiB"]
            if not isinstance(mem, int) or mem < 2048 or mem > 32768:
                errors.append("resources.memoryInMiB must be between 2048 and 32768")
        if "vcpus" in res:
            v = res["vcpus"]
            if not isinstance(v, int) or v < 1 or v > 16:
                errors.append("resources.vcpus must be between 1 and 16")
        if "diskInGiB" in res:
            d = res["diskInGiB"]
            if not isinstance(d, int) or d < 1 or d > 32:
                errors.append("resources.diskInGiB must be between 1 and 32")

    return errors


def generate_dockerfile(
    base_image: str, app_file: str, packages: list[str], port: int = 5000
) -> str:
    """
    Generate a Dockerfile string for a Lambda MicroVM image.
    """
    lines = [f"FROM {base_image}"]
    lines.append("RUN dnf install -y python3 python3-pip && dnf clean all")

    if packages:
        pkg_str = " ".join(packages)
        lines.append(f"RUN pip3 install {pkg_str}")

    lines.append(f"COPY {app_file} /app/{app_file}")
    lines.append("WORKDIR /app")
    lines.append(f'CMD ["python3", "{app_file}"]')

    return "\n".join(lines) + "\n"
