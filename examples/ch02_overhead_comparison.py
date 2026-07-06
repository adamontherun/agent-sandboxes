#!/usr/bin/env python3
"""Chapter 2 Example: Compare resource overhead of different isolation approaches.

Models four isolation strategies and calculates how many instances fit on a 64 GB host.
"""

HOST_MEMORY_GB = 64
HOST_MEMORY_MIB = HOST_MEMORY_GB * 1024  # 65536 MiB

# Each approach: (name, overhead_mib, typical_app_memory_mib, startup_ms)
APPROACHES = [
    ("Process (fork)", 0, 128, 1),
    ("Container (Docker)", 30, 128, 500),
    ("Traditional VM (QEMU/KVM)", 350, 128, 5000),
    ("Firecracker MicroVM", 5, 128, 125),
]


def max_instances(host_mib: float, overhead_mib: float, app_mib: float) -> int:
    """How many instances fit on a host, given per-instance overhead + app memory."""
    per_instance = overhead_mib + app_mib
    if per_instance == 0:
        return 0
    return int(host_mib // per_instance)


def main():
    print("=" * 78)
    print("Resource Overhead Comparison: Isolation Approaches on a 64 GB Host")
    print("=" * 78)
    print("\nAssumptions:")
    print(f"  - Host memory: {HOST_MEMORY_GB} GB ({HOST_MEMORY_MIB} MiB)")
    print("  - Application memory per instance: 128 MiB")
    print()

    header = (
        f"{'Approach':<25} {'Overhead':<12} {'Total/inst':<12} "
        f"{'Max Instances':<15} {'Startup':<10}"
    )
    print(header)
    print("-" * len(header))

    for name, overhead, app_mem, startup in APPROACHES:
        total = overhead + app_mem
        instances = max_instances(HOST_MEMORY_MIB, overhead, app_mem)
        print(
            f"{name:<25} {overhead:>4} MiB    {total:>5} MiB    "
            f"{instances:>8}        {startup:>5} ms"
        )

    print()
    print("-" * 78)
    print("Key Takeaways:")
    print("  - Firecracker adds only 5 MiB overhead vs 350 MiB for a traditional VM")
    print("  - You can run ~6x more Firecracker VMs than QEMU VMs on the same host")
    print("  - Firecracker starts 40x faster than a traditional VM")
    print("  - Containers have less overhead but share the host kernel (weaker isolation)")
    print()
    print("Sources:")
    print("  - Firecracker: <125ms startup, <5 MiB overhead, 150 VMs/sec/host")
    print("    https://github.com/firecracker-microvm/firecracker")
    print("  - AWS Lambda processes 15+ trillion invocations/month using Firecracker")


if __name__ == "__main__":
    main()
