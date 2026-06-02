from __future__ import annotations

from src.domain.billing import BillingChargePolicy
from src.use_cases.billing.policy import BillingPolicyResolver


def test_billing_policy_returns_free_retry_for_system_failure() -> None:
    resolver = BillingPolicyResolver(workflow_base_costs={"try_on": 12})

    policy = resolver.resolve_charge_policy(
        workflow_type="try_on",
        stage_name="retry_after_system_failure",
        failure_owner="system",
        recovery_kind="retry",
    )

    assert policy.charge_policy == BillingChargePolicy.FREE_RETRY
    assert policy.credits_to_charge == 0


def test_billing_policy_returns_standard_charge_for_first_successful_run() -> None:
    resolver = BillingPolicyResolver(workflow_base_costs={"product_card": 18})

    policy = resolver.resolve_charge_policy(
        workflow_type="product_card",
        stage_name="completed",
        failure_owner=None,
        recovery_kind=None,
    )

    assert policy.charge_policy == BillingChargePolicy.STANDARD
    assert policy.credits_to_charge == 18
