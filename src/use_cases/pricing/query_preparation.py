"""Deterministic query preparation for backend-owned pricing workflows."""

from __future__ import annotations

from src.domain.pricing import PricingRequest
from src.use_cases.pricing.ports import PricingBrief


def build_pricing_brief(request: PricingRequest) -> PricingBrief:
    """Build a pricing brief from the backend-owned pricing request."""
    return PricingBrief(
        product_id=request.product_id,
        target_currency=request.target_currency,
        desired_margin_percent=request.desired_margin_percent,
    )
