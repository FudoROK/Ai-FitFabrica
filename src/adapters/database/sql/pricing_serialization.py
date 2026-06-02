"""Mapping helpers between pricing SQL rows and domain records."""

from __future__ import annotations

from src.domain.pricing import (
    PricingJobRecord,
    PricingRecommendation,
    PricingRecommendationRecord,
)

from .pricing_models import PricingJobRow, PricingRecommendationRow


def job_record_from_row(row: PricingJobRow) -> PricingJobRecord:
    """Convert a SQL pricing job row into a domain job record."""
    return PricingJobRecord(
        job_id=row.job_id,
        product_id=row.product_id,
        target_currency=row.target_currency,
        desired_margin_percent=None if row.desired_margin_percent is None else float(row.desired_margin_percent),
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def recommendation_from_row(row: PricingRecommendationRow) -> PricingRecommendationRecord:
    """Convert a SQL recommendation row into a persisted domain recommendation record."""
    return PricingRecommendationRecord(
        recommendation_id=row.recommendation_id,
        job_id=row.job_id,
        recommendation=PricingRecommendation(
            recommended_price=float(row.recommended_price),
            currency=row.currency,
            rationale=row.rationale,
            market_min=float(row.market_min),
            market_avg=float(row.market_avg),
            market_max=float(row.market_max),
        ),
        created_at=row.created_at,
    )
