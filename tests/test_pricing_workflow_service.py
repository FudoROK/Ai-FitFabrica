from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.pricing import PricingComparable, PricingRequest
from src.use_cases.pricing.workflow_service import PricingWorkflowService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _RepositoryStub:
    async def create_job(self, *, request, now):
        from src.domain.pricing import PricingJobRecord

        return PricingJobRecord(
            job_id="pricing_123",
            product_id=request.product_id,
            target_currency=request.target_currency,
            desired_margin_percent=request.desired_margin_percent,
            status="accepted",
            created_at=now,
            updated_at=now,
        )

    async def save_recommendation(self, *, job_id, recommendation, now):
        from src.domain.pricing import PricingRecommendationRecord

        return PricingRecommendationRecord(
            recommendation_id="pricing_123_v1",
            job_id=job_id,
            recommendation=recommendation,
            created_at=now,
        )

    async def get_job(self, job_id: str):
        from src.domain.pricing import PricingJobRecord

        return PricingJobRecord(
            job_id=job_id,
            product_id="product-1",
            target_currency="RUB",
            desired_margin_percent=30.0,
            status="completed",
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )

    async def get_latest_recommendation(self, job_id: str):
        from src.domain.pricing import PricingRecommendation, PricingRecommendationRecord

        return PricingRecommendationRecord(
            recommendation_id=f"{job_id}_v1",
            job_id=job_id,
            recommendation=PricingRecommendation(
                recommended_price=4727.7,
                currency="RUB",
                rationale="Positioned inside the observed comparable market band.",
                market_min=3990.0,
                market_avg=4590.0,
                market_max=5990.0,
            ),
            created_at=_utc_now(),
        )

    async def mark_completed(self, job_id: str, *, now):
        from src.domain.pricing import PricingJobRecord

        return PricingJobRecord(
            job_id=job_id,
            product_id="product-1",
            target_currency="RUB",
            desired_margin_percent=30.0,
            status="completed",
            created_at=now,
            updated_at=now,
        )


class _ComparisonSourceStub:
    async def list_comparables(self, brief):
        return [
            PricingComparable(source_id="offer-1", price_amount=3990.0, currency=brief.target_currency),
            PricingComparable(source_id="offer-2", price_amount=4590.0, currency=brief.target_currency),
            PricingComparable(source_id="offer-3", price_amount=5990.0, currency=brief.target_currency),
        ]


@pytest.mark.asyncio
async def test_pricing_workflow_hydrates_comparables_and_returns_recommendation() -> None:
    service = PricingWorkflowService(
        repository=_RepositoryStub(),
        comparison_source=_ComparisonSourceStub(),
        clock=_utc_now,
    )
    result = await service.create_pricing_recommendation(
        request=PricingRequest(
            product_id="product-1",
            target_currency="RUB",
            desired_margin_percent=30.0,
        )
    )

    assert result.recommendation.recommendation.recommended_price > 0


@pytest.mark.asyncio
async def test_pricing_workflow_exposes_saved_status_and_result_queries() -> None:
    service = PricingWorkflowService(
        repository=_RepositoryStub(),
        comparison_source=_ComparisonSourceStub(),
        clock=_utc_now,
    )

    job = await service.get_job("pricing_123")
    recommendation = await service.get_result("pricing_123")

    assert job is not None
    assert job.job_id == "pricing_123"
    assert recommendation is not None
    assert recommendation.recommendation_id == "pricing_123_v1"
