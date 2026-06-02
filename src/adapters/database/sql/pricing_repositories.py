"""SQL-backed repositories for pricing workflow persistence."""

from __future__ import annotations

from sqlalchemy import select

from src.domain.pricing import PricingJobRecord, PricingRecommendation, PricingRecommendationRecord, PricingRequest

from .pricing_models import PricingJobRow, PricingRecommendationRow
from .pricing_serialization import job_record_from_row, recommendation_from_row


class SqlPricingRepository:
    """Persist pricing jobs and recommendations in portable SQL tables."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""
        self._session_factory = session_factory

    async def create_job(self, *, request: PricingRequest, now) -> PricingJobRecord:
        """Create one durable pricing job."""
        job_row = PricingJobRow(
            job_id=f"pricing_{int(now.timestamp() * 1000000)}",
            product_id=request.product_id,
            target_currency=request.target_currency,
            desired_margin_percent=request.desired_margin_percent,
            status="accepted",
            created_at=now,
            updated_at=now,
        )
        async with self._session_factory() as session:
            session.add(job_row)
            await session.commit()
        return job_record_from_row(job_row)

    async def save_recommendation(
        self,
        *,
        job_id: str,
        recommendation: PricingRecommendation,
        now,
    ) -> PricingRecommendationRecord:
        """Persist one generated pricing recommendation."""
        row = PricingRecommendationRow(
            recommendation_id=f"{job_id}_v1",
            job_id=job_id,
            recommended_price=recommendation.recommended_price,
            currency=recommendation.currency,
            rationale=recommendation.rationale,
            market_min=recommendation.market_min,
            market_avg=recommendation.market_avg,
            market_max=recommendation.market_max,
            created_at=now,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
        return recommendation_from_row(row)

    async def get_job(self, job_id: str) -> PricingJobRecord | None:
        """Return the persisted pricing job for the requested identifier."""
        async with self._session_factory() as session:
            row = await session.get(PricingJobRow, job_id)
            return None if row is None else job_record_from_row(row)

    async def get_latest_recommendation(self, job_id: str) -> PricingRecommendationRecord | None:
        """Return the latest persisted pricing recommendation for the requested job."""
        async with self._session_factory() as session:
            row = (
                await session.scalars(
                    select(PricingRecommendationRow)
                    .where(PricingRecommendationRow.job_id == job_id)
                    .order_by(PricingRecommendationRow.created_at.desc())
                )
            ).first()
            return None if row is None else recommendation_from_row(row)

    async def mark_completed(self, job_id: str, *, now) -> PricingJobRecord:
        """Mark the requested pricing job as completed."""
        async with self._session_factory() as session:
            row = await session.get(PricingJobRow, job_id)
            if row is None:
                raise LookupError(f"Unknown pricing job: {job_id}")
            row.status = "completed"
            row.updated_at = now
            await session.commit()
        return job_record_from_row(row)
