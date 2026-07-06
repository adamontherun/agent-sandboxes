"""
Chapter 4 Example: Build a MicroVM Image with CreateMicrovmImage

This script demonstrates the full workflow for building a Lambda MicroVM image:
1. Upload a code artifact to S3
2. Call CreateMicrovmImage (or UpdateMicrovmImage for subsequent versions)
3. Poll until the build completes

Prerequisites:
  - AWS CLI configured with appropriate permissions
  - An S3 bucket for code artifacts
  - A build role with S3 read + CloudWatch Logs permissions

Real output captured from a live build (account ID redacted):

    $ aws lambda-microvms create-microvm-image \
        --name ch04-hello-sandbox \
        --base-image-arn arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1 \
        --build-role-arn arn:aws:iam::<your-account-id>:role/service-role/my-build-role \
        --code-artifact uri=s3://my-bucket/ch04-hello-sandbox/artifact.zip

    {
        "imageArn": "arn:aws:lambda:us-east-1:<your-account-id>:microvm-image:ch04-hello-sandbox",
        "name": "ch04-hello-sandbox",
        "state": "CREATING",
        "createdAt": "2026-07-05T22:38:29.500000-10:00",
        "baseImageArn": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
        "baseImageVersion": "0.0",
        "buildRoleArn": "arn:aws:iam::<your-account-id>:role/service-role/my-build-role",
        "codeArtifact": {
            "uri": "s3://my-bucket/ch04-hello-sandbox/artifact.zip"
        },
        "egressNetworkConnectors": [
            "arn:aws:lambda:us-east-1:aws:network-connector:aws-network-connector:INTERNET_EGRESS"
        ],
        "resources": [{"minimumMemoryInMiB": 2048}],
        "updatedAt": "2026-07-05T22:38:29.500000-10:00",
        "imageVersion": "1.0"
    }

Build completed successfully in approximately 3 minutes. Two builds were
triggered in parallel (one per Graviton generation: 3 and 4).
"""

import json
import subprocess
import sys
import time


def run_aws(*args):
    """Run an AWS CLI command and return parsed JSON output."""
    cmd = ["aws", "lambda-microvms"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def build_image(
    name: str, bucket: str, artifact_key: str, build_role_arn: str, base_image_arn: str
):
    """Build a new MicroVM image and wait for completion."""

    s3_uri = f"s3://{bucket}/{artifact_key}"
    print(f"Building image '{name}' from {s3_uri}...")

    response = run_aws(
        "create-microvm-image",
        "--name",
        name,
        "--base-image-arn",
        base_image_arn,
        "--build-role-arn",
        build_role_arn,
        "--code-artifact",
        f"uri={s3_uri}",
    )

    image_arn = response["imageArn"]
    version = response["imageVersion"]
    print(f"Image ARN: {image_arn}")
    print(f"Version: {version}")
    print(f"State: {response['state']}")
    print()

    # Poll for completion
    print("Waiting for build to complete...")
    start = time.time()
    while True:
        status = run_aws("get-microvm-image", "--image-identifier", image_arn)
        state = status["state"]

        elapsed = time.time() - start
        print(f"  [{elapsed:.0f}s] state={state}")

        if state in ("CREATED", "UPDATED"):
            print(f"\nBuild succeeded in {elapsed:.0f} seconds!")
            return image_arn
        elif state in ("CREATE_FAILED", "UPDATE_FAILED"):
            # Check build details for the failure reason
            builds = run_aws(
                "list-microvm-image-builds",
                "--image-identifier",
                image_arn,
                "--image-version",
                version,
            )
            for build in builds.get("items", []):
                if build["buildState"] == "FAILED":
                    print(
                        f"  FAILED ({build['chipsetGeneration']}): "
                        f"{build.get('stateReason', 'unknown')}"
                    )
            sys.exit(1)

        time.sleep(15)


if __name__ == "__main__":
    import sandbox_config

    # Account-specific values come from your .env / environment — see
    # .env.example and the README's "Following along with AWS" section.
    build_image(
        name="ch04-hello-sandbox",
        bucket="my-bucket",
        artifact_key="ch04-hello-sandbox/artifact.zip",
        build_role_arn=sandbox_config.build_role_arn(),
        base_image_arn="arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
    )
