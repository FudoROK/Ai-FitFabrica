"""Workflow service for backend-owned product-card generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.billing import BillingOwnerType, LedgerEvent
from src.domain.product_card import ProductCardGarmentAnalysis, ProductCardJobRecord, ProductCardRequest, ProductCardVersionRecord


@dataclass(frozen=True)
class ProductCardSourceFile:
    """Source asset uploaded for product-card generation."""

    filename: str
    content_type: str
    payload: bytes


@dataclass(frozen=True)
class ProductCardWorkflowResult:
    """Structured workflow result returned by the orchestration service."""

    job: ProductCardJobRecord
    version: ProductCardVersionRecord
    garment_analysis: ProductCardGarmentAnalysis
    ledger_event: LedgerEvent | None = None


class ProductCardWorkflowService:
    """Orchestrate storage, generation, and persistence for product-card jobs."""

    def __init__(
        self,
        *,
        file_storage,
        repository,
        garment_identity_analyzer,
        generation_adapter,
        clock,
        billing_service=None,
        billing_owner_id: str = "public-business",
        billing_owner_type: BillingOwnerType = BillingOwnerType.BUSINESS,
    ) -> None:
        """Store explicit dependencies for product-card orchestration."""
        self._file_storage = file_storage
        self._repository = repository
        self._garment_identity_analyzer = garment_identity_analyzer
        self._generation_adapter = generation_adapter
        self._clock = clock
        self._billing_service = billing_service
        self._billing_owner_id = billing_owner_id
        self._billing_owner_type = billing_owner_type

    async def create_product_card(
        self,
        *,
        request: ProductCardRequest,
        source_files: list[ProductCardSourceFile],
    ) -> ProductCardWorkflowResult:
        """Persist source assets, generate a draft, and save the resulting version."""
        job = await self.create_product_card_job(request=request, source_files=source_files)
        return await self.execute_product_card_job(job_id=job.job_id, job=job)

    async def create_product_card_job(
        self,
        *,
        request: ProductCardRequest,
        source_files: list[ProductCardSourceFile],
    ) -> ProductCardJobRecord:
        """Persist source assets and create one accepted product-card job."""
        now: datetime = self._clock()
        asset_keys = await self._file_storage.store_many(source_files=source_files)
        return await self._repository.create_job(request=request, asset_keys=asset_keys, now=now)

    async def execute_product_card_job(
        self,
        *,
        job_id: str,
        job: ProductCardJobRecord | None = None,
    ) -> ProductCardWorkflowResult:
        """Execute generation for an existing accepted product-card job."""
        job = job or await self._repository.get_job(job_id)
        if job is None:
            raise LookupError(f"Unknown product-card job: {job_id}")
        request = ProductCardRequest(
            title_hint=job.title_hint,
            category=job.category,
            target_channel=job.target_channel,
            brand_tone=job.brand_tone,
            source_image_keys=list(job.asset_keys),
        )
        try:
            garment_analysis = await self._garment_identity_analyzer.analyze(
                job_id=job.job_id,
                asset_keys=list(job.asset_keys),
            )
            garment_analysis = await self._repository.save_garment_analysis(garment_analysis)
            draft = await self._generation_adapter.generate(request=request, garment_analysis=garment_analysis)
        except Exception:
            await self._repository.mark_failed(job.job_id, now=self._clock())
            raise
        version = await self._repository.save_generated_version(job_id=job.job_id, draft=draft, now=self._clock())
        completed_job = await self._repository.mark_completed(job.job_id, now=self._clock())
        ledger_event = await self._charge_completed_job(job_id=job.job_id)
        return ProductCardWorkflowResult(
            job=completed_job,
            version=version,
            garment_analysis=garment_analysis,
            ledger_event=ledger_event,
        )

    async def get_job(self, job_id: str) -> ProductCardJobRecord | None:
        """Return the persisted product-card job state for the requested identifier."""
        return await self._repository.get_job(job_id)

    async def get_result(self, job_id: str) -> ProductCardVersionRecord | None:
        """Return the latest generated product-card version for the requested job identifier."""
        return await self._repository.get_latest_version(job_id)

    async def get_garment_analysis(self, job_id: str) -> ProductCardGarmentAnalysis | None:
        """Return the validated saved garment analysis for one job."""
        return await self._repository.get_garment_analysis(job_id)

    async def _charge_completed_job(self, *, job_id: str) -> LedgerEvent | None:
        """Charge the completed product-card workflow through the billing core when configured."""
        if self._billing_service is None:
            return None
        return await self._billing_service.charge_workflow(
            owner_id=self._billing_owner_id,
            owner_type=self._billing_owner_type,
            workflow_type="product_card",
            workflow_reference=job_id,
            stage_name="completed",
        )
