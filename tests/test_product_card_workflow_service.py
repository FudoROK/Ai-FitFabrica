from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.product_card import ProductCardDraft, ProductCardRequest
from src.use_cases.product_card.workflow_service import ProductCardSourceFile, ProductCardWorkflowService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _FileStorageStub:
    async def store_many(self, *, source_files: list[ProductCardSourceFile]) -> list[str]:
        return [f"tenant/product-card/job-1/{source.filename}" for source in source_files]


class _RepositoryStub:
    async def create_job(self, *, request, asset_keys, now):
        from src.domain.product_card import ProductCardJobRecord

        return ProductCardJobRecord(
            job_id="product_card_123",
            status="accepted",
            target_channel=request.target_channel,
            brand_tone=request.brand_tone,
            title_hint=request.title_hint,
            asset_keys=asset_keys,
            created_at=now,
            updated_at=now,
        )

    async def save_generated_version(self, *, job_id, draft, now):
        from src.domain.product_card import ProductCardVersionRecord

        return ProductCardVersionRecord(
            version_id="product_card_123_v1",
            job_id=job_id,
            title=draft.title,
            description=draft.description,
            bullet_points=draft.bullet_points,
            attributes=draft.attributes,
            created_at=now,
        )

    async def mark_completed(self, job_id: str, *, now):
        from src.domain.product_card import ProductCardJobRecord

        return ProductCardJobRecord(
            job_id=job_id,
            status="completed",
            target_channel="wildberries",
            brand_tone="minimal premium",
            title_hint="Linen midi dress",
            asset_keys=["tenant/product-card/job-1/source-1.png"],
            created_at=now,
            updated_at=now,
        )

    async def get_job(self, job_id: str):
        from src.domain.product_card import ProductCardJobRecord

        return ProductCardJobRecord(
            job_id=job_id,
            status="completed",
            target_channel="wildberries",
            brand_tone="minimal premium",
            title_hint="Linen midi dress",
            asset_keys=["tenant/product-card/job-1/source-1.png"],
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )

    async def get_latest_version(self, job_id: str):
        from src.domain.product_card import ProductCardVersionRecord

        return ProductCardVersionRecord(
            version_id=f"{job_id}_v1",
            job_id=job_id,
            title="Linen midi dress",
            description="Breathable summer dress with a clean silhouette.",
            bullet_points=["linen blend", "midi length"],
            attributes={"category": "dress"},
            created_at=_utc_now(),
        )


class _GenerationStub:
    async def generate(self, *, request, asset_keys):
        return ProductCardDraft(
            title=request.title_hint or "Generated title",
            description=f"Generated from {len(asset_keys)} asset(s).",
            bullet_points=["linen blend", "midi length"],
            attributes={"category": "dress"},
        )


@pytest.mark.asyncio
async def test_product_card_workflow_creates_job_generates_draft_and_returns_result() -> None:
    service = ProductCardWorkflowService(
        file_storage=_FileStorageStub(),
        repository=_RepositoryStub(),
        generation_adapter=_GenerationStub(),
        clock=_utc_now,
    )

    result = await service.create_product_card(
        request=ProductCardRequest(
            title_hint="Linen midi dress",
            target_channel="wildberries",
            brand_tone="minimal premium",
        ),
        source_files=[
            ProductCardSourceFile(
                filename="source-1.png",
                content_type="image/png",
                payload=b"image-bytes",
            )
        ],
    )

    assert result.job.status == "completed"
    assert result.version.title == "Linen midi dress"


@pytest.mark.asyncio
async def test_product_card_workflow_exposes_saved_status_and_result_queries() -> None:
    service = ProductCardWorkflowService(
        file_storage=_FileStorageStub(),
        repository=_RepositoryStub(),
        generation_adapter=_GenerationStub(),
        clock=_utc_now,
    )

    job = await service.get_job("product_card_123")
    version = await service.get_result("product_card_123")

    assert job is not None
    assert job.job_id == "product_card_123"
    assert version is not None
    assert version.version_id == "product_card_123_v1"
