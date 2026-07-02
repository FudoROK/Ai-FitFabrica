from __future__ import annotations

from decimal import Decimal

from src.costs.credits_pricing_policy import CreditsPricingPolicy


def test_credits_policy_recommends_three_margin_modes() -> None:
    policy = CreditsPricingPolicy(credit_value_kzt=Decimal("50"), usd_to_kzt=Decimal("500"))

    recommendation = policy.recommend_for_action(
        product_action="B2C Try-On Basic",
        workflow_type="try_on",
        internal_cost_usd_avg=Decimal("0.20"),
    )

    assert recommendation.recommended_credits_conservative == 10
    assert recommendation.recommended_credits_balanced == 6
    assert recommendation.recommended_credits_aggressive == 4
    assert recommendation.user_price_kzt == Decimal("300")
    assert recommendation.expected_margin_percent == Decimal("66.67")


def test_credits_policy_keeps_failed_system_repair_free() -> None:
    policy = CreditsPricingPolicy()

    assert policy.should_charge(failure_owner="system", recovery_kind="repair") is False
    assert policy.should_charge(failure_owner="system", recovery_kind="retry") is False
    assert policy.should_charge(failure_owner=None, recovery_kind=None) is True
