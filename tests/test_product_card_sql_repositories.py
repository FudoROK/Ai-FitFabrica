from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.product_card_repositories import SqlProductCardRepository
from src.domain.product_card import ProductCardDraft, ProductCardGarmentAnalysis, ProductCardRequest


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_product_card_repository_persists_job_and_latest_version() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlProductCardRepository(session_factory=session_factory)

    aggregate = await repository.create_job(
        request=ProductCardRequest(
            title_hint="Linen midi dress",
            target_channel="wildberries",
            brand_tone="minimal premium",
        ),
        asset_keys=["tenant/product-card/job-1/source-1.png"],
        now=_utc_now(),
    )
    await repository.save_generated_version(
        job_id=aggregate.job_id,
        draft=ProductCardDraft(
            title="Linen midi dress",
            description="Breathable summer dress with a clean silhouette.",
            bullet_points=["linen blend", "midi length"],
            attributes={"category": "dress"},
        ),
        now=_utc_now(),
    )
    latest = await repository.get_latest_version(aggregate.job_id)
    analysis = ProductCardGarmentAnalysis(
        job_id=aggregate.job_id,
        invocation_id="garment-invocation-1",
        prompt_version="garment_identity.v1",
        contract_version="garment_identity.contract.v1",
        garment_type="dress",
        dominant_color="blue",
        silhouette_summary="Midi dress.",
        confidence=0.92,
        uncertainty_level="low",
    )
    await repository.save_garment_analysis(analysis)
    loaded_analysis = await repository.get_garment_analysis(aggregate.job_id)

    assert aggregate.target_channel == "wildberries"
    assert latest is not None
    assert latest.title == "Linen midi dress"
    assert loaded_analysis == analysis

    loaded_job = await repository.get_job(aggregate.job_id)

    assert loaded_job is not None
    assert loaded_job.job_id == aggregate.job_id

    await engine.dispose()
