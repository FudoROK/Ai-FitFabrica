from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.content_package_repositories import SqlContentPackageRepository
from src.domain.content_package import ContentPackageOption, ContentPackageRequest


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_content_package_repository_persists_job_and_package_version() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlContentPackageRepository(session_factory=session_factory)

    try:
        job = await repository.create_job(
            request=ContentPackageRequest(
                product_card_version_id="product_card_123_v1",
                package_name="marketplace-launch",
                requested_channels=["wildberries", "instagram"],
            ),
            now=_utc_now(),
        )
        version = await repository.save_package_version(
            job_id=job.job_id,
            package_name="marketplace-launch",
            assets=[
                ContentPackageOption(asset_kind="caption", label="Instagram caption"),
                ContentPackageOption(asset_kind="listing", label="Marketplace listing"),
            ],
            artifact_keys=[
                "fitfabrica/tenants/public/content-package/job-1/caption.txt",
                "fitfabrica/tenants/public/content-package/job-1/listing.json",
            ],
            now=_utc_now(),
        )

        assert version.job_id == job.job_id
        assert len(version.assets) == 2
    finally:
        await engine.dispose()
