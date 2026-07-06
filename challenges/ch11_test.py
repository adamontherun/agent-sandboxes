"""Tests for Chapter 11 challenge: multi-tenant sandbox routing."""

import pytest
from ch11 import IsolationRouter, RoutingDecision


class TestDedicatedTier:
    def test_first_call_not_reused(self):
        router = IsolationRouter(pool_size=2)
        decision = router.route("acme", tier="dedicated")
        assert decision.dedicated is True
        assert decision.reused is False
        assert decision.cleaned is False

    def test_second_call_reuses_same_microvm(self):
        router = IsolationRouter(pool_size=2)
        d1 = router.route("acme", tier="dedicated")
        d2 = router.route("acme", tier="dedicated")
        assert d2.reused is True
        assert d2.microvm_id == d1.microvm_id

    def test_different_tenants_get_different_microvms(self):
        router = IsolationRouter(pool_size=2)
        d1 = router.route("acme", tier="dedicated")
        d2 = router.route("globex", tier="dedicated")
        assert d1.microvm_id != d2.microvm_id

    def test_result_is_dataclass(self):
        router = IsolationRouter(pool_size=2)
        result = router.route("acme", tier="dedicated")
        assert isinstance(result, RoutingDecision)

    def test_evict_removes_dedicated_assignment(self):
        router = IsolationRouter(pool_size=2)
        router.route("acme", tier="dedicated")
        assert router.evict_dedicated("acme") is True

    def test_evict_unknown_tenant_returns_false(self):
        router = IsolationRouter(pool_size=2)
        assert router.evict_dedicated("nobody") is False

    def test_route_after_evict_gets_fresh_microvm(self):
        router = IsolationRouter(pool_size=2)
        d1 = router.route("acme", tier="dedicated")
        router.evict_dedicated("acme")
        d2 = router.route("acme", tier="dedicated")
        assert d2.reused is False
        assert d2.microvm_id != d1.microvm_id


class TestSharedTier:
    def test_first_call_not_reused_not_cleaned(self):
        router = IsolationRouter(pool_size=2)
        decision = router.route("user-1", tier="shared")
        assert decision.dedicated is False
        assert decision.reused is False
        assert decision.cleaned is False

    def test_same_tenant_reuses_slot(self):
        router = IsolationRouter(pool_size=2)
        d1 = router.route("user-1", tier="shared")
        d2 = router.route("user-1", tier="shared")
        assert d2.reused is True
        assert d2.microvm_id == d1.microvm_id
        assert d2.cleaned is False

    def test_pool_fills_before_evicting(self):
        router = IsolationRouter(pool_size=2)
        d1 = router.route("user-1", tier="shared")
        d2 = router.route("user-2", tier="shared")
        assert d1.microvm_id != d2.microvm_id
        assert d1.cleaned is False
        assert d2.cleaned is False

    def test_pool_full_evicts_lru_slot_and_cleans(self):
        router = IsolationRouter(pool_size=2)
        router.route("user-1", tier="shared")
        router.route("user-2", tier="shared")
        d3 = router.route("user-3", tier="shared")
        assert d3.cleaned is True

    def test_evicted_slot_reused_by_new_owner(self):
        router = IsolationRouter(pool_size=2)
        d1 = router.route("user-1", tier="shared")
        router.route("user-2", tier="shared")
        d3 = router.route("user-3", tier="shared")
        # user-3 took over user-1's slot since user-1 was least-recently assigned.
        assert d3.microvm_id == d1.microvm_id

    def test_original_owner_gets_new_slot_after_eviction(self):
        router = IsolationRouter(pool_size=2)
        router.route("user-1", tier="shared")
        router.route("user-2", tier="shared")
        router.route("user-3", tier="shared")  # evicts user-1's slot
        d = router.route("user-1", tier="shared")
        assert d.reused is False
