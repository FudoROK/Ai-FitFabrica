"""Backend-owned workflow pricing and free retry/repair policy rules."""

from __future__ import annotations

from src.domain.billing import BillingChargePolicy, ResolvedBillingPolicy


class BillingPolicyResolver:
    """Resolve workflow charge policy from backend-owned pricing rules."""

    def __init__(self, workflow_base_costs: dict[str, int]) -> None:
        """Store the base workflow credit costs used for policy resolution."""
        self._workflow_base_costs = workflow_base_costs

    def resolve_charge_policy(
        self,
        *,
        workflow_type: str,
        stage_name: str,
        failure_owner: str | None,
        recovery_kind: str | None,
    ) -> ResolvedBillingPolicy:
        """Return the applicable charge policy for the requested workflow step."""
        if failure_owner == "system" and recovery_kind == "retry":
            return ResolvedBillingPolicy(
                charge_policy=BillingChargePolicy.FREE_RETRY,
                credits_to_charge=0,
            )
        if failure_owner == "system" and recovery_kind == "repair":
            return ResolvedBillingPolicy(
                charge_policy=BillingChargePolicy.FREE_REPAIR,
                credits_to_charge=0,
            )
        if workflow_type not in self._workflow_base_costs:
            raise KeyError(f"Unknown workflow pricing policy: {workflow_type} at {stage_name}")
        return ResolvedBillingPolicy(
            charge_policy=BillingChargePolicy.STANDARD,
            credits_to_charge=self._workflow_base_costs[workflow_type],
        )
