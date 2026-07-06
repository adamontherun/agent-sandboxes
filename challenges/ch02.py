"""Chapter 2 Challenge: Firecracker MicroVM Capacity Planning."""


def calculate_max_vms(host_memory_gb: float, vm_overhead_mib: float, vm_memory_mib: float) -> int:
    """Calculate the maximum number of VMs that fit on a host."""
    raise NotImplementedError


def estimate_startup_time(num_vms: int, creation_rate_per_sec: float) -> float:
    """Estimate wall-clock time to start a batch of VMs sequentially."""
    raise NotImplementedError


def compare_isolation_approaches(workload_count: int, host_memory_gb: float) -> dict:
    """Compare how many workloads each isolation approach can support."""
    raise NotImplementedError
