"""
Runnable example: a multi-tenant session router in front of MicroVMs.

This SIMULATES the AWS Lambda MicroVMs boundary locally — there is no real
RunMicrovm/SuspendMicrovm call here, just a MockMicrovmClient standing in for
one. The point of this example is the routing/isolation *logic* an
orchestrator needs on top of the real API from Chapters 5-6: which tenant
gets a dedicated instance, when a shared instance is reused, and what
"cleaning state between users" has to mean on a shared instance since the
real MicroVM boundary isn't cleaning it for you in that case.

No AWS calls are made. Real `aws lambda-microvms` command shapes are in
Chapters 4-6; this script is pure Python so it can run anywhere.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field


class MockMicrovmClient:
    """Stands in for the real AWS Lambda MicroVMs API for this example.

    Each method mirrors a real operation (RunMicrovm, TerminateMicrovm) but
    just tracks state in memory instead of calling AWS.
    """

    def __init__(self) -> None:
        self._next_id = 1
        self.launched: set[str] = set()
        self.terminated: set[str] = set()

    def run_microvm(self) -> str:
        microvm_id = f"microvm-mock-{self._next_id:04d}"
        self._next_id += 1
        self.launched.add(microvm_id)
        return microvm_id

    def terminate_microvm(self, microvm_id: str) -> None:
        self.launched.discard(microvm_id)
        self.terminated.add(microvm_id)

    def reset_workspace(self, microvm_id: str) -> None:
        """Simulates wiping a shared instance's writable state between
        tenants (Chapter 9's file-system-isolation concerns, applied at the
        multi-tenant boundary instead of the single-tenant one)."""
        pass


@dataclass
class TenantSession:
    tenant_id: str
    microvm_id: str
    dedicated: bool
    last_used: float = field(default_factory=time.monotonic)


class SessionRouter:
    """Routes tenant requests to MicroVMs under one of two isolation modes.

    - dedicated tenants get their own MicroVM, created on first use and
      reused on every subsequent request until evicted.
    - non-dedicated ("shared-pool") tenants are routed to one of a small
      pool of shared MicroVMs; the pool is reset between distinct tenants
      to prevent state leaking from one user to the next.
    """

    def __init__(self, client: MockMicrovmClient, shared_pool_size: int = 2) -> None:
        self.client = client
        self.shared_pool_size = shared_pool_size
        self.dedicated_sessions: dict[str, TenantSession] = {}
        self.shared_pool: list[str] = []
        self.shared_pool_owner: dict[str, str | None] = {}

    def route(self, tenant_id: str, dedicated: bool) -> TenantSession:
        if dedicated:
            return self._route_dedicated(tenant_id)
        return self._route_shared(tenant_id)

    def _route_dedicated(self, tenant_id: str) -> TenantSession:
        session = self.dedicated_sessions.get(tenant_id)
        if session is not None:
            session.last_used = time.monotonic()
            return session
        microvm_id = self.client.run_microvm()
        session = TenantSession(tenant_id=tenant_id, microvm_id=microvm_id, dedicated=True)
        self.dedicated_sessions[tenant_id] = session
        return session

    def _route_shared(self, tenant_id: str) -> TenantSession:
        # Already own a slot in the pool: reuse it, no cleanup needed.
        for microvm_id, owner in self.shared_pool_owner.items():
            if owner == tenant_id:
                return TenantSession(tenant_id=tenant_id, microvm_id=microvm_id, dedicated=False)

        # Grow the pool if under capacity.
        if len(self.shared_pool) < self.shared_pool_size:
            microvm_id = self.client.run_microvm()
            self.shared_pool.append(microvm_id)
            self.shared_pool_owner[microvm_id] = tenant_id
            return TenantSession(tenant_id=tenant_id, microvm_id=microvm_id, dedicated=False)

        # Pool is full: evict the least-recently-assigned slot and clean it.
        microvm_id = self.shared_pool.pop(0)
        self.shared_pool.append(microvm_id)
        previous_owner = self.shared_pool_owner.get(microvm_id)
        self.client.reset_workspace(microvm_id)
        self.shared_pool_owner[microvm_id] = tenant_id
        print(
            f"  [cleanup] {microvm_id} reassigned {previous_owner!r} -> "
            f"{tenant_id!r}, workspace reset"
        )
        return TenantSession(tenant_id=tenant_id, microvm_id=microvm_id, dedicated=False)

    def evict_dedicated(self, tenant_id: str) -> None:
        session = self.dedicated_sessions.pop(tenant_id, None)
        if session is not None:
            self.client.terminate_microvm(session.microvm_id)


def main() -> None:
    client = MockMicrovmClient()
    router = SessionRouter(client, shared_pool_size=2)

    print("== Dedicated tenants: one MicroVM each, reused across requests ==")
    for tenant in ["enterprise-acme", "enterprise-globex"]:
        s1 = router.route(tenant, dedicated=True)
        s2 = router.route(tenant, dedicated=True)
        print(
            f"  {tenant}: first={s1.microvm_id} second={s2.microvm_id} "
            f"(same instance reused: {s1.microvm_id == s2.microvm_id})"
        )

    print("\n== Shared pool: free-tier tenants share a small pool of MicroVMs ==")
    free_tenants = ["free-user-1", "free-user-2", "free-user-3", "free-user-1"]
    for tenant in free_tenants:
        session = router.route(tenant, dedicated=False)
        print(f"  {tenant} -> {session.microvm_id}")

    print("\n== Evicting a dedicated tenant terminates its MicroVM ==")
    router.evict_dedicated("enterprise-acme")
    print(f"  terminated: {sorted(client.terminated)}")
    print(f"  still launched: {sorted(client.launched)}")


if __name__ == "__main__":
    main()
