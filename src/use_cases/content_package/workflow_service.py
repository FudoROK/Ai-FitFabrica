"""Workflow service for backend-owned content-package generation."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.billing import BillingOwnerType, LedgerEvent
from src.domain.content_package import (
    ContentPackageJobRecord,
    ContentPackageRequest,
    ContentPackageVersionRecord,
)


@dataclass(frozen=True)
class ContentPackageWorkflowResult:
    """Structured workflow result returned by the content-package service."""

    job: ContentPackageJobRecord
    version: ContentPackageVersionRecord
    ledger_event: LedgerEvent | None = None


class ContentPackageWorkflowService:
    """Orchestrate generation, artifact persistence, and workflow storage for content packages."""

    def __init__(
        self,
        *,
        repository,
        artifact_storage,
        generation_adapter,
        clock,
        billing_service=None,
        billing_owner_id: str = "public-business",
        billing_owner_type: BillingOwnerType = BillingOwnerType.BUSINESS,
    ) -> None:
        """Store explicit dependencies for content-package orchestration."""
        self._repository = repository
        self._artifact_storage = artifact_storage
        self._generation_adapter = generation_adapter
        self._clock = clock
        self._billing_service = billing_service
        self._billing_owner_id = billing_owner_id
        self._billing_owner_type = billing_owner_type

    async def create_content_package(self, *, request: ContentPackageRequest) -> ContentPackageWorkflowResult:
        """Generate one content package, persist its artifacts, and save the resulting version."""
        job = await self.create_content_package_job(request=request)
        return await self.execute_content_package_job(job_id=job.job_id, job=job)

    async def create_content_package_job(self, *, request: ContentPackageRequest) -> ContentPackageJobRecord:
        """Create one accepted content-package job without running generation."""
        now = self._clock()
        return await self._repository.create_job(request=request, now=now)

    async def execute_content_package_job(
        self,
        *,
        job_id: str,
        job: ContentPackageJobRecord | None = None,
    ) -> ContentPackageWorkflowResult:
        """Execute generation for an existing accepted content-package job."""
        job = job or await self._repository.get_job(job_id)
        if job is None:
            raise LookupError(f"Unknown content-package job: {job_id}")
        request = ContentPackageRequest(
            product_card_version_id=job.product_card_version_id,
            package_name=job.package_name,
            requested_channels=list(job.requested_channels),
        )
        assets = await self._generation_adapter.generate(request=request)
        artifact_keys = await self._artifact_storage.store_generated_assets(job_id=job.job_id, assets=assets)
        version = await self._repository.save_package_version(
            job_id=job.job_id,
            package_name=request.package_name,
            assets=assets,
            artifact_keys=artifact_keys,
            now=self._clock(),
        )
        completed_job = await self._repository.mark_completed(job.job_id, now=self._clock())
        ledger_event = await self._charge_completed_job(job_id=job.job_id)
        return ContentPackageWorkflowResult(job=completed_job, version=version, ledger_event=ledger_event)

    async def get_job(self, job_id: str) -> ContentPackageJobRecord | None:
        """Return the persisted content-package job for the requested identifier."""
        return await self._repository.get_job(job_id)

    async def get_result(self, job_id: str) -> ContentPackageVersionRecord | None:
        """Return the latest generated content-package version for the requested job identifier."""
        return await self._repository.get_latest_version(job_id)

    async def _charge_completed_job(self, *, job_id: str) -> LedgerEvent | None:
        """Charge the completed content-package workflow through the billing core when configured."""
        if self._billing_service is None:
            return None
        return await self._billing_service.charge_workflow(
            owner_id=self._billing_owner_id,
            owner_type=self._billing_owner_type,
            workflow_type="content_package",
            workflow_reference=job_id,
            stage_name="completed",
        )
