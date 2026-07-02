from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.product_card import ProductCardDraft, ProductCardGarmentAnalysis, ProductCardRequest
from src.use_cases.product_card.workflow_service import ProductCardSourceFile, ProductCardWorkflowService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _FileStorageStub:
    async def store_many(self, *, source_files: list[ProductCardSourceFile]) -> list[str]:
        return [f"tenant/product-card/job-1/{source.filename}" for source in source_files]


class _RepositoryStub:
    failed_job_ids: list[str] = []
    saved_analyses: list[ProductCardGarmentAnalysis] = []

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

    async def save_garment_analysis(self, analysis):
        self.saved_analyses.append(analysis)
        return analysis

    async def get_garment_analysis(self, job_id):
        return next((item for item in self.saved_analyses if item.job_id == job_id), None)

    async def mark_failed(self, job_id: str, *, now):
        self.failed_job_ids.append(job_id)
        job = await self.get_job(job_id)
        return job.model_copy(update={"status": "failed", "updated_at": now})

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
    received_analysis = None

    async def generate(self, *, request, garment_analysis):
        self.received_analysis = garment_analysis
        return ProductCardDraft(
            title=request.title_hint or "Generated title",
            description=f"Generated from {garment_analysis.garment_type}.",
            bullet_points=["linen blend", "midi length"],
            attributes={"category": "dress"},
        )


class _FailingGenerationStub:
    async def generate(self, *, request, garment_analysis):
        raise RuntimeError("provider failed")


class _GarmentAnalysisStub:
    async def analyze(self, *, job_id, asset_keys):
        return ProductCardGarmentAnalysis(
            job_id=job_id,
            invocation_id="garment-invocation-1",
            prompt_version="garment_identity.v1",
            contract_version="garment_identity.contract.v1",
            garment_type="dress",
            dominant_color="blue",
            silhouette_summary="Midi dress.",
            confidence=0.95,
            uncertainty_level="low",
        )


class _FailingGarmentAnalysisStub:
    async def analyze(self, *, job_id, asset_keys):
        raise RuntimeError("garment analysis failed")


@pytest.mark.asyncio
async def test_product_card_workflow_creates_job_generates_draft_and_returns_result() -> None:
    service = ProductCardWorkflowService(
        file_storage=_FileStorageStub(),
        repository=_RepositoryStub(),
        garment_identity_analyzer=_GarmentAnalysisStub(),
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
        garment_identity_analyzer=_GarmentAnalysisStub(),
        generation_adapter=_GenerationStub(),
        clock=_utc_now,
    )

    job = await service.get_job("product_card_123")
    version = await service.get_result("product_card_123")

    assert job is not None
    assert job.job_id == "product_card_123"
    assert version is not None
    assert version.version_id == "product_card_123_v1"


@pytest.mark.asyncio
async def test_product_card_workflow_marks_job_failed_when_generation_fails() -> None:
    repository = _RepositoryStub()
    repository.failed_job_ids = []
    repository.saved_analyses = []
    service = ProductCardWorkflowService(
        file_storage=_FileStorageStub(),
        repository=repository,
        garment_identity_analyzer=_GarmentAnalysisStub(),
        generation_adapter=_FailingGenerationStub(),
        clock=_utc_now,
    )

    with pytest.raises(RuntimeError, match="provider failed"):
        await service.execute_product_card_job(job_id="product_card_123")

    assert repository.failed_job_ids == ["product_card_123"]


@pytest.mark.asyncio
async def test_product_card_workflow_persists_garment_analysis_before_generation() -> None:
    repository = _RepositoryStub()
    repository.saved_analyses = []
    generation = _GenerationStub()
    service = ProductCardWorkflowService(
        file_storage=_FileStorageStub(),
        repository=repository,
        garment_identity_analyzer=_GarmentAnalysisStub(),
        generation_adapter=generation,
        clock=_utc_now,
    )

    await service.execute_product_card_job(job_id="product_card_123")

    assert repository.saved_analyses[0].garment_type == "dress"
    assert generation.received_analysis == repository.saved_analyses[0]


@pytest.mark.asyncio
async def test_product_card_workflow_blocks_generation_when_garment_analysis_fails() -> None:
    repository = _RepositoryStub()
    repository.failed_job_ids = []
    generation = _GenerationStub()
    service = ProductCardWorkflowService(
        file_storage=_FileStorageStub(),
        repository=repository,
        garment_identity_analyzer=_FailingGarmentAnalysisStub(),
        generation_adapter=generation,
        clock=_utc_now,
    )

    with pytest.raises(RuntimeError, match="garment analysis failed"):
        await service.execute_product_card_job(job_id="product_card_123")

    assert generation.received_analysis is None
    assert repository.failed_job_ids == ["product_card_123"]
