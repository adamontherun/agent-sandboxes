"""
Chapter 5 Example: Launch a MicroVM and make an authenticated request

This script demonstrates:
1. RunMicrovm with a complete idle policy
2. Polling GetMicrovm until RUNNING
3. Creating an auth token with CreateMicrovmAuthToken
4. Making an authenticated HTTPS request to the MicroVM endpoint

Real output captured from a live run (account ID and token redacted):

    $ aws lambda-microvms run-microvm \
        --image-identifier arn:aws:lambda:us-east-1:<your-account-id>:microvm-image:lambda-microvms-poc-hello-world \
        --execution-role-arn arn:aws:iam::<your-account-id>:role/MicroVMLambdaPOCRole \
        --idle-policy '{"maxIdleDurationSeconds":300,"suspendedDurationSeconds":300,"autoResumeEnabled":true}'

    {
        "microvmId": "microvm-29fabacb-68fe-30ed-b477-39bf36e55b16",
        "state": "PENDING",
        "endpoint": "<random-id>.lambda-microvm.us-east-1.on.aws",
        "imageArn": "arn:aws:lambda:us-east-1:<your-account-id>:microvm-image:lambda-microvms-poc-hello-world",
        "imageVersion": "11.0",
        "executionRoleArn": "arn:aws:iam::<your-account-id>:role/MicroVMLambdaPOCRole",
        "idlePolicy": {
            "maxIdleDurationSeconds": 300,
            "suspendedDurationSeconds": 300,
            "autoResumeEnabled": true
        },
        "maximumDurationInSeconds": 28800,
        "startedAt": "2026-07-05T21:43:41.138000-10:00",
        "ingressNetworkConnectors": [
            "arn:aws:lambda:us-east-1:aws:network-connector:aws-network-connector:HTTP_INGRESS"
        ],
        "egressNetworkConnectors": [
            "arn:aws:lambda:us-east-1:aws:network-connector:aws-network-connector:INTERNET_EGRESS"
        ]
    }

GetMicrovm showed state=RUNNING within 5 seconds of the RunMicrovm call.
"""

import json
import time
import subprocess
import sys
import urllib.request
import ssl


def run_aws(*args):
    """Run an AWS CLI command and return parsed JSON output."""
    cmd = ["aws", "lambda-microvms"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout) if result.stdout.strip() else {}


def launch_microvm(image_arn: str, execution_role_arn: str):
    """Launch a MicroVM and wait for it to reach RUNNING state."""

    # All three idle policy fields are required together.
    # Omitting any one produces a validation error.
    idle_policy = json.dumps({
        "maxIdleDurationSeconds": 300,
        "suspendedDurationSeconds": 300,
        "autoResumeEnabled": True,
    })

    print("Launching MicroVM...")
    response = run_aws(
        "run-microvm",
        "--image-identifier", image_arn,
        "--execution-role-arn", execution_role_arn,
        "--idle-policy", idle_policy,
    )

    microvm_id = response["microvmId"]
    endpoint = response["endpoint"]
    print(f"  MicroVM ID: {microvm_id}")
    print(f"  Endpoint:   https://{endpoint}")
    print(f"  State:      {response['state']}")
    print()

    # Wait for RUNNING
    print("Waiting for RUNNING state...")
    for _ in range(20):
        time.sleep(3)
        status = run_aws("get-microvm", "--microvm-identifier", microvm_id)
        state = status["state"]
        print(f"  state={state}")
        if state == "RUNNING":
            break
    else:
        print("ERROR: MicroVM did not reach RUNNING in time")
        sys.exit(1)

    return microvm_id, endpoint


def create_auth_token(microvm_id: str, port: int = 5000):
    """Create an auth token for a specific port."""

    # allowedPorts is a tagged union: each entry has exactly ONE of
    # "port", "range", or "allPorts". No "protocol" field exists.
    allowed_ports = json.dumps([{"port": port}])

    print(f"Creating auth token for port {port}...")
    response = run_aws(
        "create-microvm-auth-token",
        "--microvm-identifier", microvm_id,
        "--expiration-in-minutes", "15",
        "--allowed-ports", allowed_ports,
    )

    token = response["authToken"]["X-aws-proxy-auth"]
    print(f"  Token (first 40 chars): {token[:40]}...")
    print(f"  Token type: JWE (5 base64url segments)")
    return token


def make_request(endpoint: str, token: str, path: str = "/"):
    """Make an authenticated HTTPS request to the MicroVM."""

    url = f"https://{endpoint}{path}"
    print(f"\nRequesting {url}...")

    req = urllib.request.Request(url)
    req.add_header("X-aws-proxy-auth", token)

    try:
        ctx = ssl.create_default_context()
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        body = resp.read().decode()
        print(f"  Status: {resp.status}")
        print(f"  Body:   {body}")
    except Exception as e:
        print(f"  Request failed: {e}")
        print("  (This is expected if running from a network-restricted environment)")


def cleanup(microvm_id: str):
    """Terminate the MicroVM."""
    print(f"\nTerminating {microvm_id}...")
    run_aws("terminate-microvm", "--microvm-identifier", microvm_id)
    print("  Terminated.")


if __name__ == "__main__":
    IMAGE_ARN = "arn:aws:lambda:us-east-1:<your-account-id>:microvm-image:lambda-microvms-poc-hello-world"
    ROLE_ARN = "arn:aws:iam::<your-account-id>:role/MicroVMLambdaPOCRole"

    microvm_id, endpoint = launch_microvm(IMAGE_ARN, ROLE_ARN)
    try:
        token = create_auth_token(microvm_id)
        make_request(endpoint, token)
    finally:
        cleanup(microvm_id)
