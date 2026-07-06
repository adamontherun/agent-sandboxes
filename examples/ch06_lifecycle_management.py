"""
Chapter 6 Example: Full MicroVM lifecycle management

Demonstrates: launch -> suspend -> resume -> terminate
with real state verification at each step.

Real output captured from a live run (account ID redacted):

    Suspend and Resume both return NO response body on success.
    State transitions are confirmed via GetMicrovm:
      - After suspend-microvm + ~3s: state=SUSPENDED
      - After resume-microvm + ~3s: state=RUNNING
      - After terminate-microvm: state=TERMINATED

    Terminated instances in ListMicrovms retain only:
      microvmId, state, imageArn, imageVersion, startedAt
    Fields like endpoint, executionRoleArn, idlePolicy, and
    networkConnectors are absent from the list view.
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
        return None
    return json.loads(result.stdout) if result.stdout.strip() else {}


def wait_for_state(microvm_id: str, target_state: str, timeout: int = 30):
    """Poll GetMicrovm until target state is reached."""
    for _ in range(timeout // 3):
        time.sleep(3)
        status = run_aws("get-microvm", "--microvm-identifier", microvm_id)
        if status and status.get("state") == target_state:
            return status
    raise TimeoutError(f"Did not reach {target_state} within {timeout}s")


def full_lifecycle_demo(image_arn: str, execution_role_arn: str):
    """Run through the complete MicroVM lifecycle."""

    idle_policy = json.dumps(
        {
            "maxIdleDurationSeconds": 300,
            "suspendedDurationSeconds": 300,
            "autoResumeEnabled": True,
        }
    )

    # 1. Launch
    print("=" * 60)
    print("STEP 1: Launch MicroVM")
    print("=" * 60)
    response = run_aws(
        "run-microvm",
        "--image-identifier",
        image_arn,
        "--execution-role-arn",
        execution_role_arn,
        "--idle-policy",
        idle_policy,
    )
    microvm_id = response["microvmId"]
    print(f"  ID: {microvm_id}")
    print(f"  Initial state: {response['state']}")

    status = wait_for_state(microvm_id, "RUNNING")
    print("  Confirmed: state=RUNNING")
    print()

    # 2. Suspend
    print("=" * 60)
    print("STEP 2: Suspend MicroVM")
    print("=" * 60)
    print("  Calling suspend-microvm...")
    result = run_aws("suspend-microvm", "--microvm-identifier", microvm_id)
    print(f"  Response body: {result}")  # Empty dict - no body returned
    status = wait_for_state(microvm_id, "SUSPENDED")
    print("  Confirmed: state=SUSPENDED")
    print()

    # 3. Resume
    print("=" * 60)
    print("STEP 3: Resume MicroVM")
    print("=" * 60)
    print("  Calling resume-microvm...")
    result = run_aws("resume-microvm", "--microvm-identifier", microvm_id)
    print(f"  Response body: {result}")  # Empty dict - no body returned
    status = wait_for_state(microvm_id, "RUNNING")
    print("  Confirmed: state=RUNNING")
    print()

    # 4. Terminate
    print("=" * 60)
    print("STEP 4: Terminate MicroVM")
    print("=" * 60)
    print("  Calling terminate-microvm...")
    result = run_aws("terminate-microvm", "--microvm-identifier", microvm_id)
    print(f"  Response body: {result}")  # Empty dict - no body returned
    time.sleep(3)
    status = run_aws("get-microvm", "--microvm-identifier", microvm_id)
    print(f"  Confirmed: state={status['state']}")
    print()

    # 5. Verify cleanup
    print("=" * 60)
    print("STEP 5: Verify in ListMicrovms")
    print("=" * 60)
    all_vms = run_aws("list-microvms")
    for vm in all_vms.get("items", []):
        if vm["microvmId"] == microvm_id:
            print(f"  Found in list: state={vm['state']}")
            print(f"  Fields present: {list(vm.keys())}")
            # Note: endpoint, idlePolicy, networkConnectors are absent
            # for terminated instances
            break

    print("\nLifecycle demo complete.")


if __name__ == "__main__":
    import sandbox_config

    # Account-specific values come from your .env / environment — see
    # .env.example and the README's "Following along with AWS" section.
    full_lifecycle_demo(sandbox_config.image_arn(), sandbox_config.execution_role_arn())
