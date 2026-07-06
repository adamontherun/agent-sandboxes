"""Tests for Chapter 2 challenge functions."""

import pytest
import sys
import os

# Allow importing from both challenges/ and solutions/
sys.path.insert(0, os.path.dirname(__file__))


def get_module():
    """Import the solution if USE_SOLUTION is set, otherwise the challenge."""
    if os.environ.get("USE_SOLUTION"):
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "solutions"))
        import ch02 as mod
    else:
        import ch02 as mod
    return mod


class TestCalculateMaxVMs:
    def test_firecracker_64gb(self):
        mod = get_module()
        # 64 GB = 65536 MiB, each VM uses 5 + 128 = 133 MiB
        result = mod.calculate_max_vms(64, 5, 128)
        assert result == 492  # floor(65536 / 133)

    def test_traditional_vm_64gb(self):
        mod = get_module()
        # Each VM uses 350 + 128 = 478 MiB
        result = mod.calculate_max_vms(64, 350, 128)
        assert result == 137  # floor(65536 / 478)

    def test_zero_overhead(self):
        mod = get_module()
        # Process isolation: 0 overhead, 128 MiB per workload
        result = mod.calculate_max_vms(64, 0, 128)
        assert result == 512  # floor(65536 / 128)

    def test_small_host(self):
        mod = get_module()
        result = mod.calculate_max_vms(1, 5, 128)
        assert result == 7  # floor(1024 / 133)


class TestEstimateStartupTime:
    def test_150_vms_at_150_per_sec(self):
        mod = get_module()
        result = mod.estimate_startup_time(150, 150)
        assert result == pytest.approx(1.0)

    def test_300_vms_at_150_per_sec(self):
        mod = get_module()
        result = mod.estimate_startup_time(300, 150)
        assert result == pytest.approx(2.0)

    def test_single_vm(self):
        mod = get_module()
        result = mod.estimate_startup_time(1, 150)
        assert result == pytest.approx(1 / 150)

    def test_zero_vms(self):
        mod = get_module()
        result = mod.estimate_startup_time(0, 150)
        assert result == pytest.approx(0.0)


class TestCompareIsolationApproaches:
    def test_returns_all_keys(self):
        mod = get_module()
        result = mod.compare_isolation_approaches(100, 64)
        assert set(result.keys()) == {"process", "container", "traditional_vm", "firecracker"}

    def test_firecracker_can_fit_400(self):
        mod = get_module()
        result = mod.compare_isolation_approaches(400, 64)
        assert result["firecracker"]["can_fit"] is True
        assert result["firecracker"]["max_instances"] == 492

    def test_traditional_vm_cannot_fit_400(self):
        mod = get_module()
        result = mod.compare_isolation_approaches(400, 64)
        assert result["traditional_vm"]["can_fit"] is False
        assert result["traditional_vm"]["max_instances"] == 137

    def test_memory_used_calculation(self):
        mod = get_module()
        result = mod.compare_isolation_approaches(100, 64)
        # Firecracker: 100 * (5 + 128) = 13300 MiB
        assert result["firecracker"]["memory_used_mib"] == pytest.approx(13300)
        # Container: 100 * (30 + 128) = 15800 MiB
        assert result["container"]["memory_used_mib"] == pytest.approx(15800)
