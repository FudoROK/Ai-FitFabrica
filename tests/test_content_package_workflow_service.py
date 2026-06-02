from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.content_package import ContentPackageOption, ContentPackageRequest
from src.use_cases.content_package.workflow_service import ContentPackageWorkflowService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _RepositoryStub:
    async def create_job(self, *, request, now):
        from src.domain.content_package import ContentPackageJobRecord

        return ContentPackageJobRecord(
            job_id="content_package_123",
            product_card_version_id=request.product_card_version_id,
            package_name=request.package_name,
            status="accepted",
            requested_channels=list(request.requested_channels),
            created_at=now,
            updated_at=now,
        )

    async def save_package_version(self, *, job_id, package_name, assets, artifact_keys, now):
        from src.domain.content_package import ContentPackageVersionRecord

        return ContentPackageVersionRecord(
            version_id="content_package_123_v1",
            job_id=job_id,
            package_name=package_name,
            assets=list(assets),
            created_at=now,
        )

    async def mark_completed(self, job_id: str, *, now):
        from src.domain.content_package import ContentPackageJobRecord

        return ContentPackageJobRecord(
            job_id=job_id,
            product_card_version_id="product_card_123_v1",
            package_name="marketplace-launch",
            status="completed",
            requested_channels=["wildberries", "instagram"],
            created_at=now,
            updated_at=now,
        )

    async def get_job(self, job_id: str):
        from src.domain.content_package import ContentPackageJobRecord

        return ContentPackageJobRecord(
            job_id=job_id,
            product_card_version_id="product_card_123_v1",
            package_name="marketplace-launch",
            status="completed",
            requested_channels=["wildberries", "instagram"],
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )

    async def get_latest_version(self, job_id: str):
        from src.domain.content_package import ContentPackageVersionRecord

        return ContentPackageVersionRecord(
            version_id=f"{job_id}_v1",
            job_id=job_id,
            package_name="marketplace-launch",
            assets=[
                ContentPackageOption(asset_kind="caption", label="Instagram caption"),
                ContentPackageOption(asset_kind="listing", label="Marketplace listing"),
            ],
            created_at=_utc_now(),
        )


class _ArtifactStorageStub:
    async def store_generated_assets(self, *, job_id, assets):
        return [f"fitfabrica/tenants/public/content-package/{job_id}/{asset.asset_kind}" for asset in assets]


class _GenerationStub:
    async def generate(self, *, request):
        return [
            ContentPackageOption(asset_kind="caption", label="Instagram caption"),
            ContentPackageOption(asset_kind="listing", label="Marketplace listing"),
        ]


@pytest.mark.asyncio
async def test_content_package_workflow_creates_package_and_returns_artifact_references() -> None:
    service = ContentPackageWorkflowService(
        repository=_RepositoryStub(),
        artifact_storage=_ArtifactStorageStub(),
        generation_adapter=_GenerationStub(),
        clock=_utc_now,
    )

    result = await service.create_content_package(
        request=ContentPackageRequest(
            product_card_version_id="product_card_123_v1",
            package_name="marketplace-launch",
            requested_channels=["wildberries", "instagram"],
        )
    )

    assert result.version.package_name == "marketplace-launch"
    assert result.version.assets


@pytest.mark.asyncio
async def test_content_package_workflow_exposes_saved_status_and_result_queries() -> None:
    service = ContentPackageWorkflowService(
        repository=_RepositoryStub(),
        artifact_storage=_ArtifactStorageStub(),
        generation_adapter=_GenerationStub(),
        clock=_utc_now,
    )

    job = await service.get_job("content_package_123")
    version = await service.get_result("content_package_123")

    assert job is not None
    assert job.job_id == "content_package_123"
    assert version is not None
    assert version.version_id == "content_package_123_v1"
