"""
Solution: Multi-tenant sandbox router.
"""

from dataclasses import dataclass


@dataclass
class RoutingDecision:
    """Result of routing a tenant to a MicroVM slot."""

    microvm_id: str
    dedicated: bool
    reused: bool
    cleaned: bool = False


class IsolationRouter:
    """Routes tenants to MicroVMs under two isolation tiers: dedicated
    (one MicroVM per tenant, held indefinitely until evicted) and shared
    (a fixed-size pool, reassigned least-recently-assigned-first, cleaned
    on every reassignment to a different tenant)."""

    def __init__(self, pool_size: int = 2) -> None:
        self.pool_size = pool_size
        self._next_id = 1
        self._dedicated: dict[str, str] = {}
        # slots is a list of pool indices in least-recently-assigned order;
        # the front is the next candidate for eviction.
        self._slot_owner: dict[int, str | None] = {i: None for i in range(pool_size)}
        self._slot_order: list[int] = list(range(pool_size))
        self._tenant_slot: dict[str, int] = {}

    def _new_id(self) -> str:
        value = self._next_id
        self._next_id += 1
        return f"id-{value}"

    def route(self, tenant_id: str, tier: str) -> RoutingDecision:
        if tier == "dedicated":
            return self._route_dedicated(tenant_id)
        return self._route_shared(tenant_id)

    def _route_dedicated(self, tenant_id: str) -> RoutingDecision:
        if tenant_id in self._dedicated:
            return RoutingDecision(
                microvm_id=self._dedicated[tenant_id],
                dedicated=True,
                reused=True,
                cleaned=False,
            )
        microvm_id = f"dedicated-{tenant_id}-{self._new_id()}"
        self._dedicated[tenant_id] = microvm_id
        return RoutingDecision(microvm_id=microvm_id, dedicated=True, reused=False, cleaned=False)

    def _route_shared(self, tenant_id: str) -> RoutingDecision:
        if tenant_id in self._tenant_slot:
            slot = self._tenant_slot[tenant_id]
            self._touch_slot(slot)
            return RoutingDecision(
                microvm_id=f"shared-slot-{slot}",
                dedicated=False,
                reused=True,
                cleaned=False,
            )

        # Prefer an empty slot if one exists.
        for slot in self._slot_order:
            if self._slot_owner[slot] is None:
                self._assign_slot(slot, tenant_id)
                return RoutingDecision(
                    microvm_id=f"shared-slot-{slot}",
                    dedicated=False,
                    reused=False,
                    cleaned=False,
                )

        # Pool full: evict the least-recently-assigned slot.
        slot = self._slot_order[0]
        self._assign_slot(slot, tenant_id)
        return RoutingDecision(
            microvm_id=f"shared-slot-{slot}",
            dedicated=False,
            reused=False,
            cleaned=True,
        )

    def _assign_slot(self, slot: int, tenant_id: str) -> None:
        previous_owner = self._slot_owner[slot]
        if previous_owner is not None:
            del self._tenant_slot[previous_owner]
        self._slot_owner[slot] = tenant_id
        self._tenant_slot[tenant_id] = slot
        self._touch_slot(slot)

    def _touch_slot(self, slot: int) -> None:
        self._slot_order.remove(slot)
        self._slot_order.append(slot)

    def evict_dedicated(self, tenant_id: str) -> bool:
        if tenant_id in self._dedicated:
            del self._dedicated[tenant_id]
            return True
        return False
