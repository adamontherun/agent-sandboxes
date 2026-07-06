"""
Challenge: Build a multi-user sandbox router.

Implement IsolationRouter to decide, per tenant, whether to route to a
dedicated MicroVM or a slot in a shared pool, and to clean shared state when
a slot changes owners. See book/chapters/ch11.html for details.
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
    """Routes tenants to MicroVMs under two isolation tiers.

    - Dedicated tenants (tier="dedicated") always get their own MicroVM,
      created on first use and reused on every later request for that
      tenant.
    - Shared tenants (tier="shared") are routed into a fixed-size pool.
      Each pool slot is identified by an integer index 0..pool_size-1.
      A tenant that already owns a slot reuses it. Otherwise, an empty
      slot is used if one exists. If the pool is full, the least-recently
      assigned slot is reassigned to the new tenant, and that reassignment
      MUST count as "cleaned" (state from the previous owner must not leak
      to the new one).

    Track slot assignment order yourself (e.g. a list of slot indices in
    least-recently-assigned order) so you can identify which slot to evict.
    """

    def __init__(self, pool_size: int = 2) -> None:
        self.pool_size = pool_size
        self._next_id = 1
        # TODO: whatever bookkeeping you need for dedicated + shared tiers.

    def route(self, tenant_id: str, tier: str) -> RoutingDecision:
        """
        Route a tenant request to a MicroVM.

        tier is "dedicated" or "shared".

        Returns a RoutingDecision with:
          - microvm_id: a string identifier for the assigned MicroVM/slot.
            Dedicated tenants get ids like "dedicated-<tenant_id>". Shared
            slots get ids like "shared-slot-<index>".
          - dedicated: True iff tier == "dedicated".
          - reused: True iff this tenant already owned this exact
            microvm_id/slot from a previous call.
          - cleaned: True iff this call reassigned a shared slot away from
            a different tenant (i.e. state needed cleaning). Always False
            for dedicated tenants and for a shared slot's first assignment.
        """
        raise NotImplementedError("Implement IsolationRouter.route()")

    def evict_dedicated(self, tenant_id: str) -> bool:
        """
        Remove a dedicated tenant's MicroVM assignment entirely (simulates
        TerminateMicrovm). Returns True if the tenant had a dedicated
        assignment to remove, False otherwise. A subsequent route() call
        for this tenant with tier="dedicated" must allocate a fresh
        microvm_id (reused=False).
        """
        raise NotImplementedError("Implement IsolationRouter.evict_dedicated()")
