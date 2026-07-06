"""Tests for Chapter 4 challenge: validate_create_image_params and generate_dockerfile"""

from ch04 import generate_dockerfile, validate_create_image_params


class TestValidateCreateImageParams:
    def test_valid_minimal_params(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert errors == []

    def test_missing_name(self):
        params = {
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert any("name" in e.lower() for e in errors)

    def test_missing_base_image_arn(self):
        params = {
            "name": "my-image",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert any("base_image_arn" in e.lower() for e in errors)

    def test_missing_build_role_arn(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert any("build_role_arn" in e.lower() for e in errors)

    def test_missing_code_artifact(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
        }
        errors = validate_create_image_params(params)
        assert any("code_artifact" in e.lower() for e in errors)

    def test_invalid_name_too_long(self):
        params = {
            "name": "a" * 65,
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert any("name" in e.lower() for e in errors)

    def test_invalid_name_special_chars(self):
        params = {
            "name": "my image!",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert any("name" in e.lower() for e in errors)

    def test_invalid_base_image_arn_format(self):
        params = {
            "name": "my-image",
            "base_image_arn": "not-an-arn",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert any("base_image_arn" in e.lower() for e in errors)

    def test_invalid_build_role_arn_format(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "not-an-arn",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
        }
        errors = validate_create_image_params(params)
        assert any("build_role_arn" in e.lower() for e in errors)

    def test_code_artifact_missing_uri(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {},
        }
        errors = validate_create_image_params(params)
        assert any("code_artifact" in e.lower() for e in errors)

    def test_code_artifact_extra_keys(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://bucket/file.zip", "extra": "bad"},
        }
        errors = validate_create_image_params(params)
        assert any("code_artifact" in e.lower() for e in errors)

    def test_valid_with_resources(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
            "resources": {"memoryInMiB": 4096, "vcpus": 2, "diskInGiB": 10},
        }
        errors = validate_create_image_params(params)
        assert errors == []

    def test_memory_too_high(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
            "resources": {"memoryInMiB": 65536},
        }
        errors = validate_create_image_params(params)
        assert any("memory" in e.lower() for e in errors)

    def test_vcpus_too_high(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
            "resources": {"vcpus": 32},
        }
        errors = validate_create_image_params(params)
        assert any("vcpu" in e.lower() for e in errors)

    def test_disk_too_high(self):
        params = {
            "name": "my-image",
            "base_image_arn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
            "build_role_arn": "arn:aws:iam::123456789012:role/MyBuildRole",
            "code_artifact": {"uri": "s3://my-bucket/artifact.zip"},
            "resources": {"diskInGiB": 64},
        }
        errors = validate_create_image_params(params)
        assert any("disk" in e.lower() for e in errors)


class TestGenerateDockerfile:
    def test_contains_from(self):
        result = generate_dockerfile(
            "public.ecr.aws/lambda/microvms:al2023-minimal", "app.py", ["flask"]
        )
        assert "FROM public.ecr.aws/lambda/microvms:al2023-minimal" in result

    def test_contains_copy(self):
        result = generate_dockerfile(
            "public.ecr.aws/lambda/microvms:al2023-minimal", "app.py", ["flask"]
        )
        assert "COPY" in result
        assert "app.py" in result

    def test_contains_pip_install(self):
        result = generate_dockerfile(
            "public.ecr.aws/lambda/microvms:al2023-minimal", "app.py", ["flask", "requests"]
        )
        assert "pip" in result.lower()
        assert "flask" in result
        assert "requests" in result

    def test_contains_cmd(self):
        result = generate_dockerfile(
            "public.ecr.aws/lambda/microvms:al2023-minimal", "server.py", ["fastapi"]
        )
        assert "CMD" in result or "ENTRYPOINT" in result
        assert "server.py" in result

    def test_empty_packages(self):
        result = generate_dockerfile("public.ecr.aws/lambda/microvms:al2023-minimal", "app.py", [])
        assert "FROM" in result
        assert "app.py" in result
