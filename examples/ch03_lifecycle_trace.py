#!/usr/bin/env python3
"""
Chapter 3 - Lambda MicroVM Lifecycle Trace

Traces a MicroVM through its full lifecycle using the real AWS Lambda
MicroVMs CLI commands. Each step prints the command that would be run and an
illustrative response whose shape matches the actual API.

This is a teaching tool - no real AWS calls are made. To run these commands
for real against your own account, see Chapters 4-6 and the README's
"Following along with AWS" section.
"""

import json
from datetime import UTC, datetime

import sandbox_config

# Identifiers for the traced commands. These default to fake but
# realistic-looking values; set AWS_ACCOUNT_ID / AWS_REGION in your .env
# (see .env.example) to see the trace with your own account and region.
ACCOUNT_ID = sandbox_config.ACCOUNT_ID
REGION = sandbox_config.REGION
IMAGE_NAME = "agent-sandbox-v1"
IMAGE_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:microvm-image:{IMAGE_NAME}"
BASE_IMAGE_ARN = f"arn:aws:lambda:{REGION}:aws:microvm-image:al2023-1"
BUILD_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/MicroVMBuildRole"
EXECUTION_ROLE_ARN = f"arn:aws:iam::{ACCOUNT_ID}:role/MicroVMExecutionRole"
HTTP_INGRESS = f"arn:aws:lambda:{REGION}:aws:network-connector:aws-network-connector:HTTP_INGRESS"
INTERNET_EGRESS = (
    f"arn:aws:lambda:{REGION}:aws:network-connector:aws-network-connector:INTERNET_EGRESS"
)

MICROVM_ID = "microvm-0a1b2c3d-4e5f-6789-0abc-def012345678"
ENDPOINT = f"5acf9c8f-6477-3ee3-3993-6ea1fee66713.lambda-microvm.{REGION}.on.aws"
AUTH_TOKEN = "eyJraWQiOiJkMzQ3ZGQ5Ni1lZDM2LTQ1MzA...mock-jwe-token"

# A MicroVM's maximum lifetime before automatic termination (8 hours),
# reported by run-microvm/get-microvm as maximumDurationInSeconds.
MAX_DURATION_SECONDS = 28800


def separator():
    print("\n" + "=" * 72 + "\n")


def step(number, title):
    print(f"{'─' * 72}")
    print(f"  STEP {number}: {title}")
    print(f"{'─' * 72}")


def show_command(cmd):
    print(f"\n  $ {cmd}\n")


def show_response(data):
    print("  Response (illustrative):")
    formatted = json.dumps(data, indent=4)
    for line in formatted.split("\n"):
        print(f"    {line}")
    print()


def show_no_response():
    print("  Response: (empty body — this operation returns no content)\n")


def microvm_state(state):
    """The shape get-microvm / run-microvm return, with the given state."""
    return {
        "microvmId": MICROVM_ID,
        "state": state,
        "endpoint": ENDPOINT,
        "imageArn": IMAGE_ARN,
        "imageVersion": "1.0",
        "executionRoleArn": EXECUTION_ROLE_ARN,
        "idlePolicy": {
            "maxIdleDurationSeconds": 300,
            "suspendedDurationSeconds": 300,
            "autoResumeEnabled": True,
        },
        "maximumDurationInSeconds": MAX_DURATION_SECONDS,
        "startedAt": "2026-07-05T10:05:00Z",
        "ingressNetworkConnectors": [HTTP_INGRESS],
        "egressNetworkConnectors": [INTERNET_EGRESS],
    }


def main():
    print("Lambda MicroVM Lifecycle Trace")
    print("=" * 72)
    print("This script traces a MicroVM through its full lifecycle.")
    print("All responses are illustrative - no real AWS calls are made.")
    print(f"Timestamp: {datetime.now(UTC).isoformat()}")

    # Step 1: Create the image
    separator()
    step(1, "Create a MicroVM image from a Dockerfile + code artifact")
    show_command(
        "aws lambda-microvms create-microvm-image \\\n"
        f"    --name {IMAGE_NAME} \\\n"
        "    --code-artifact uri=s3://my-bucket/app.zip \\\n"
        f"    --base-image-arn {BASE_IMAGE_ARN} \\\n"
        f"    --build-role-arn {BUILD_ROLE_ARN}"
    )
    show_response(
        {
            "imageArn": IMAGE_ARN,
            "name": IMAGE_NAME,
            "state": "CREATING",
            "createdAt": "2026-07-05T10:00:00Z",
        }
    )
    print(f"  Build logs stream to CloudWatch: /aws/lambda-microvms/{IMAGE_NAME}")
    print("  The service runs your Dockerfile, boots the app, and snapshots it.")

    # Step 2: Image build completes
    separator()
    step(2, "Image build completes (snapshot created)")
    show_command(f"aws lambda-microvms get-microvm-image --image-identifier {IMAGE_NAME}")
    show_response(
        {
            "imageArn": IMAGE_ARN,
            "name": IMAGE_NAME,
            "state": "CREATED",
            "latestActiveImageVersion": "1.0",
            "createdAt": "2026-07-05T10:00:00Z",
            "updatedAt": "2026-07-05T10:03:42Z",
        }
    )
    print("  The snapshot captures the booted OS, packages, and running app.")
    print("  Future launches restore from this snapshot instantly.")

    # Step 3: Run a MicroVM from the image
    separator()
    step(3, "Run a MicroVM instance from the image")
    show_command(
        "aws lambda-microvms run-microvm \\\n"
        f"    --image-identifier {IMAGE_ARN} \\\n"
        f"    --execution-role-arn {EXECUTION_ROLE_ARN} \\\n"
        f'    --ingress-network-connectors "{HTTP_INGRESS}" \\\n'
        f'    --egress-network-connectors "{INTERNET_EGRESS}" \\\n'
        '    --idle-policy \'{"maxIdleDurationSeconds":300,'
        '"suspendedDurationSeconds":300,"autoResumeEnabled":true}\''
    )
    show_response(microvm_state("PENDING"))
    print("  Sizing (memory, vCPU) is fixed at image-creation time, not here.")
    print("  The response has no auth token — you mint one separately (Step 5).")

    # Step 4: Wait for RUNNING
    separator()
    step(4, "Poll until the MicroVM reaches RUNNING")
    show_command(f"aws lambda-microvms get-microvm --microvm-identifier {MICROVM_ID}")
    show_response(microvm_state("RUNNING"))
    print("  Snapshots skip the boot sequence, so RUNNING arrives in seconds.")

    # Step 5: Mint a token and call the app
    separator()
    step(5, "Create an auth token and call the application over HTTPS")
    show_command(
        "aws lambda-microvms create-microvm-auth-token \\\n"
        f"    --microvm-identifier {MICROVM_ID} \\\n"
        "    --expiration-in-minutes 15 \\\n"
        "    --allowed-ports '[{\"port\":8080}]'"
    )
    show_response({"authToken": {"X-aws-proxy-auth": AUTH_TOKEN}})
    print("  /health below is your application's own route, not an AWS API.")
    show_command(
        "curl \\\n"
        f'    -H "X-aws-proxy-auth: {AUTH_TOKEN[:30]}..." \\\n'
        f"    https://{ENDPOINT}/health"
    )
    show_response({"status": "ok"})
    print("  Requests carry the token in the X-aws-proxy-auth header.")

    # Step 6: Idle and auto-suspend
    separator()
    step(6, "MicroVM goes idle, then suspends automatically")
    print("  After 300s with no requests, the idle policy triggers suspension.")
    print()
    show_command(f"aws lambda-microvms get-microvm --microvm-identifier {MICROVM_ID}")
    show_response(microvm_state("SUSPENDED"))
    print("  Memory and disk are frozen and preserved. No compute billing.")

    # Step 7: Resume
    separator()
    step(7, "Resume the MicroVM (explicit, or automatic on the next request)")
    show_command(f"aws lambda-microvms resume-microvm --microvm-identifier {MICROVM_ID}")
    show_no_response()
    print("  resume-microvm returns no body; poll get-microvm to confirm RUNNING.")
    show_command(f"aws lambda-microvms get-microvm --microvm-identifier {MICROVM_ID}")
    show_response(microvm_state("RUNNING"))
    print("  State is restored exactly — memory, disk, and running processes.")
    print("  With autoResumeEnabled, this happens transparently on the next request.")

    # Step 8: Terminate
    separator()
    step(8, "Terminate the MicroVM when the session is complete")
    show_command(f"aws lambda-microvms terminate-microvm --microvm-identifier {MICROVM_ID}")
    show_no_response()
    print("  terminate-microvm returns no body; a follow-up get-microvm shows:")
    show_response(microvm_state("TERMINATED") | {"terminatedAt": "2026-07-05T12:35:00Z"})
    print("  The MicroVM is permanently stopped and all state is discarded.")

    separator()
    print("LIFECYCLE SUMMARY")
    print()
    print("  Image:   CREATING --> CREATED")
    print("  MicroVM: PENDING --> RUNNING --> SUSPENDED --> RUNNING --> TERMINATED")
    print("            (launch)   (active)    (frozen)      (resumed)   (done)")
    print()
    print("Key takeaways:")
    print("  - Snapshots enable instant launch (no boot sequence)")
    print("  - State persists across suspend/resume cycles")
    print("  - Suspended VMs cost nothing in compute")
    print("  - Each VM gets a unique endpoint + short-lived JWE token")
    print("  - Maximum lifetime is 8 hours (maximumDurationInSeconds: 28800)")
    print()


if __name__ == "__main__":
    main()
