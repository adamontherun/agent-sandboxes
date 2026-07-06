"""Chapter 2 Solution: Firecracker MicroVM Capacity Planning."""


def calculate_max_vms(host_memory_gb: float, vm_overhead_mib: float, vm_memory_mib: float) -> int:
    """Calculate the maximum number of VMs that fit on a host."""
    host_memory_mib = host_memory_gb * 1024
    per_vm = vm_overhead_mib + vm_memory_mib
    if per_vm == 0:
        return 0
    return int(host_memory_mib // per_vm)


def estimate_startup_time(num_vms: int, creation_rate_per_sec: float) -> float:
    """Estimate wall-clock time to start a batch of VMs sequentially."""
    return num_vms / creation_rate_per_sec


def compare_isolation_approaches(workload_count: int, host_memory_gb: float) -> dict:
    """Compare how many workloads each isolation approach can support."""
    approaches = {
        "process": (0, 128),
        "container": (30, 128),
        "traditional_vm": (350, 128),
        "firecracker": (5, 128),
    }
    result = {}
    for name, (overhead, app_mem) in approaches.items():
        max_inst = calculate_max_vms(host_memory_gb, overhead, app_mem)
        memory_used = workload_count * (overhead + app_mem)
        result[name] = {
            "max_instances": max_inst,
            "can_fit": workload_count <= max_inst,
            "memory_used_mib": float(memory_used),
        }
    return result
