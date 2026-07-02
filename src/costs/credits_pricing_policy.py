"""Credits pricing recommendations derived from workflow internal costs."""

from __future__ import annotations

from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP

from pydantic import BaseModel, ConfigDict, Field


class CreditsPricingRecommendation(BaseModel):
    """Recommended credits for one product action under three margin modes."""

    model_config = ConfigDict(extra="forbid")

    product_action: str = Field(min_length=1)
    workflow_type: str = Field(min_length=1)
    direct_cost_usd_avg: Decimal
    internal_cost_kzt_avg: Decimal
    recommended_credits_conservative: int = Field(ge=0)
    recommended_credits_balanced: int = Field(ge=0)
    recommended_credits_aggressive: int = Field(ge=0)
    user_price_kzt: Decimal
    expected_margin_percent: Decimal


class CreditsPricingPolicy:
    """Recommend FitFabrica Credits prices without mutating billing rules."""

    def __init__(
        self,
        *,
        credit_value_kzt: Decimal = Decimal("50"),
        usd_to_kzt: Decimal = Decimal("500"),
    ) -> None:
        """Store currency conversion assumptions."""

        self._credit_value_kzt = credit_value_kzt
        self._usd_to_kzt = usd_to_kzt

    def recommend_for_action(
        self,
        *,
        product_action: str,
        workflow_type: str,
        internal_cost_usd_avg: Decimal,
    ) -> CreditsPricingRecommendation:
        """Return conservative, balanced, and aggressive credit recommendations."""

        internal_cost_kzt = _money_kzt(internal_cost_usd_avg * self._usd_to_kzt)
        conservative = self._credits_for(internal_cost_kzt=internal_cost_kzt, multiplier=Decimal("5"))
        balanced = self._credits_for(internal_cost_kzt=internal_cost_kzt, multiplier=Decimal("3"))
        aggressive = self._credits_for(internal_cost_kzt=internal_cost_kzt, multiplier=Decimal("2"))
        user_price_kzt = Decimal(balanced) * self._credit_value_kzt
        margin = Decimal("0.00")
        if user_price_kzt > 0:
            margin = ((user_price_kzt - internal_cost_kzt) / user_price_kzt * Decimal("100")).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        return CreditsPricingRecommendation(
            product_action=product_action,
            workflow_type=workflow_type,
            direct_cost_usd_avg=internal_cost_usd_avg,
            internal_cost_kzt_avg=internal_cost_kzt,
            recommended_credits_conservative=conservative,
            recommended_credits_balanced=balanced,
            recommended_credits_aggressive=aggressive,
            user_price_kzt=user_price_kzt,
            expected_margin_percent=margin,
        )

    @staticmethod
    def should_charge(*, failure_owner: str | None, recovery_kind: str | None) -> bool:
        """Return whether the user should pay for this workflow outcome."""

        if failure_owner == "system" and recovery_kind in {"repair", "retry"}:
            return False
        return True

    def _credits_for(self, *, internal_cost_kzt: Decimal, multiplier: Decimal) -> int:
        credits = (internal_cost_kzt * multiplier / self._credit_value_kzt).to_integral_value(rounding=ROUND_CEILING)
        return int(max(Decimal("0"), credits))


def _money_kzt(value: Decimal) -> Decimal:
    """Normalize KZT amounts to two decimals."""

    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
