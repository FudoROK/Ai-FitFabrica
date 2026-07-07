from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.pricing_repositories import SqlPricingRepository
from src.domain.pricing import PricingRecommendation, PricingRequest


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_pricing_repository_persists_job_and_recommendation() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlPricingRepository(session_factory=session_factory)

    try:
        job = await repository.create_job(
            request=PricingRequest(
                product_id="product-1",
                target_currency="RUB",
                desired_margin_percent=30.0,
            ),
            now=_utc_now(),
        )
        recommendation = await repository.save_recommendation(
            job_id=job.job_id,
            recommendation=PricingRecommendation(
                recommended_price=4490.0,
                currency="RUB",
                rationale="Positioned slightly below premium comparable cluster.",
                market_min=3990.0,
                market_avg=4590.0,
                market_max=5990.0,
            ),
            now=_utc_now(),
        )

        assert recommendation.job_id == job.job_id
    finally:
        await engine.dispose()
