"""Backend-owned ranking logic for pricing recommendations."""

from __future__ import annotations

from src.domain.pricing import PricingRecommendation


def recommend_price(
    *,
    comparables: list[float],
    desired_margin_percent: float | None,
    currency: str,
) -> PricingRecommendation:
    """Build a deterministic pricing recommendation from comparable market evidence."""
    if not comparables:
        raise ValueError("pricing comparables are required")

    ordered = sorted(comparables)
    market_min = ordered[0]
    market_max = ordered[-1]
    middle = len(ordered) // 2
    if len(ordered) % 2 == 1:
        market_avg = ordered[middle]
    else:
        market_avg = round((ordered[middle - 1] + ordered[middle]) / 2, 2)
    markup_factor = 1.0 if desired_margin_percent is None else 1.0 + (desired_margin_percent / 1000.0)
    recommended_price = min(market_max, max(market_min, round(market_avg * markup_factor, 2)))
    return PricingRecommendation(
        recommended_price=recommended_price,
        currency=currency,
        rationale="Positioned inside the observed comparable market band.",
        market_min=market_min,
        market_avg=market_avg,
        market_max=market_max,
    )
