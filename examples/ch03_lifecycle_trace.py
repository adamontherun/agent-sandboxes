#!/usr/bin/env python3
"""
Chapter 3 - Lambda MicroVM Lifecycle Trace

Simulates the full lifecycle of a Lambda MicroVM using mock AWS CLI commands.
Each step prints the command that would be run and an illustrative response.

This is a teaching tool - no real AWS calls are made.
"""

import json
import time
from datetime import datetime, timezone

# Fake but realistic-looking identifiers
ACCOUNT_ID = "123456789012"
REGION = "us-east-1"
IMAGE_NAME = "agent-sandbox-v1"
IMAGE_ARN = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:microvm-image:{IMAGE_NAME}"
MICROVM_ID = "mvm-0a1b2c3d4e5f67890"
ENDPOINT_URL = f"https://{MICROVM_ID}.microvm.lambda.{REGION}.amazonaws.com"
AUTH_TOKEN = "eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkEyNTZHQ00ifQ.mock-jwe-token..."


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


def main():
    print("Lambda MicroVM Lifecycle Trace")
    print("=" * 72)
    print("This script traces a MicroVM through its full lifecycle.")
    print("All responses are illustrative - no real AWS calls are made.")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

    # Step 1: Create Image
    separator()
    step(1, "Create a MicroVM image from Dockerfile + code artifact")
    show_command(
        "aws lambda create-microvm-image \\\n"
        "    --image-name agent-sandbox-v1 \\\n"
        "    --dockerfile-uri s3://my-bucket/sandbox/Dockerfile \\\n"
        "    --code-uri s3://my-bucket/sandbox/agent-code.tar.gz \\\n"
        "    --base-image arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1"
    )
    show_response({
        "ImageArn": IMAGE_ARN,
        "ImageName": IMAGE_NAME,
        "Status": "BUILDING",
        "CreatedAt": "2026-07-05T10:00:00Z",
        "BaseImage": "arn:aws:lambda:us-east-1:aws:microvm-image:al2023-1",
    })
    print("  Build logs stream to CloudWatch: /aws/lambda/microvms/agent-sandbox-v1")
    print("  The service builds the Dockerfile, boots the image, and takes a snapshot.")

    # Step 2: Image ready
    separator()
    step(2, "Image build completes (snapshot created)")
    show_command("aws lambda get-microvm-image --image-name agent-sandbox-v1")
    show_response({
        "ImageArn": IMAGE_ARN,
        "ImageName": IMAGE_NAME,
        "Status": "READY",
        "Architecture": "arm64",
        "SnapshotSizeBytes": 2_147_483_648,
        "CreatedAt": "2026-07-05T10:00:00Z",
        "ReadyAt": "2026-07-05T10:03:42Z",
    })
    print("  The snapshot includes booted OS, installed packages, and code artifact.")
    print("  Future launches restore from this snapshot instantly.")

    # Step 3: Run MicroVM
    separator()
    step(3, "Run a MicroVM instance from the image")
    show_command(
        "aws lambda run-microvm \\\n"
        f"    --image-arn {IMAGE_ARN} \\\n"
        "    --vcpus 4 --memory-mb 8192 --disk-gb 16 \\\n"
        '    --idle-policy \'{"maxIdleDurationSeconds":300,"autoResumeEnabled":true}\''
    )
    show_response({
        "MicrovmId": MICROVM_ID,
        "Status": "RUNNING",
        "EndpointUrl": ENDPOINT_URL,
        "AuthToken": AUTH_TOKEN,
        "VCpus": 4,
        "MemoryMb": 8192,
        "DiskGb": 16,
        "IdlePolicy": {
            "maxIdleDurationSeconds": 300,
            "autoResumeEnabled": True,
        },
        "LaunchedAt": "2026-07-05T10:05:00Z",
    })
    print("  The MicroVM is now running with a unique endpoint URL.")
    print("  Use the AuthToken in the X-aws-proxy-auth header for all requests.")

    # Step 4: Execute code
    separator()
    step(4, "Execute code inside the MicroVM via HTTP")
    show_command(
        f'curl -X POST \\\n'
        f'    -H "X-aws-proxy-auth: {AUTH_TOKEN[:30]}..." \\\n'
        f'    -H "Content-Type: application/json" \\\n'
        f'    -d \'{{"command": "python -c \\"import pandas; print(pandas.__version__)\\"}}\' \\\n'
        f'    {ENDPOINT_URL}/exec'
    )
    show_response({
        "exitCode": 0,
        "stdout": "2.2.1\n",
        "stderr": "",
        "durationMs": 342,
    })
    print("  The MicroVM executed the command and returned results.")
    print("  State (installed packages, files) persists for future requests.")

    # Step 5: Idle and suspend
    separator()
    step(5, "MicroVM goes idle, then suspends automatically")
    print("  After 300 seconds with no requests, the idle policy triggers suspension.")
    print()
    show_command(f"aws lambda get-microvm --microvm-id {MICROVM_ID}")
    show_response({
        "MicrovmId": MICROVM_ID,
        "Status": "SUSPENDED",
        "SuspendedAt": "2026-07-05T10:10:00Z",
        "EndpointUrl": ENDPOINT_URL,
        "Note": "No compute charges while suspended. State is preserved.",
    })
    print("  Memory, disk, and processes are frozen. No compute billing.")

    # Step 6: Resume
    separator()
    step(6, "Resume the MicroVM (explicit or automatic on next request)")
    show_command(f"aws lambda resume-microvm --microvm-id {MICROVM_ID}")
    show_response({
        "MicrovmId": MICROVM_ID,
        "Status": "RUNNING",
        "ResumedAt": "2026-07-05T11:30:00Z",
        "EndpointUrl": ENDPOINT_URL,
        "Note": "All state restored - memory, disk, running processes.",
    })
    print("  The VM picks up exactly where it left off.")
    print("  With autoResumeEnabled, this happens transparently on the next HTTP request.")

    # Step 7: Refresh auth token
    separator()
    step(7, "Refresh authentication token (tokens are short-lived)")
    show_command(f"aws lambda create-microvm-auth-token --microvm-id {MICROVM_ID}")
    show_response({
        "MicrovmId": MICROVM_ID,
        "AuthToken": "eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkEyNTZHQ00ifQ.new-token...",
        "ExpiresAt": "2026-07-05T12:30:00Z",
    })
    print("  Use the new token in subsequent X-aws-proxy-auth headers.")

    # Step 8: Terminate
    separator()
    step(8, "Terminate the MicroVM when the session is complete")
    show_command(f"aws lambda terminate-microvm --microvm-id {MICROVM_ID}")
    show_response({
        "MicrovmId": MICROVM_ID,
        "Status": "TERMINATED",
        "TerminatedAt": "2026-07-05T12:35:00Z",
    })
    print("  The MicroVM is permanently stopped. All state is discarded.")
    print("  To start a new session, call RunMicrovm again from the same image.")

    separator()
    print("LIFECYCLE SUMMARY")
    print()
    print("  CREATING --> RUNNING --> IDLE --> SUSPENDED --> RUNNING --> TERMINATED")
    print("    (build)    (active)   (quiet)   (frozen)     (resumed)   (done)")
    print()
    print("Key takeaways:")
    print("  - Snapshots enable instant launch (no boot sequence)")
    print("  - State persists across suspend/resume cycles")
    print("  - Suspended VMs cost nothing in compute")
    print("  - Each VM gets a unique endpoint + short-lived JWE token")
    print("  - Max runtime: 8 hours | Max: 16 vCPUs, 32 GB RAM, 32 GB disk")
    print()


if __name__ == "__main__":
    main()
