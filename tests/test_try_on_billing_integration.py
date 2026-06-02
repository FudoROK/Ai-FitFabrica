from __future__ import annotations

from datetime import datetime, timezone

import pytest
from starlette.datastructures import UploadFile

from src.adapters.billing.in_memory_repository import InMemoryBillingRepository
from src.domain.billing import BillingOwnerType
from src.domain.try_on import TryOnChargeStatus, TryOnSandboxLifecycleMode, TryOnStoredInput, TryOnUploadRole
from src.use_cases.billing.policy import BillingPolicyResolver
from src.use_cases.billing.service import BillingService
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _RepositoryStub:
    async def save(self, job):
        self.saved = job

    async def get(self, job_id: str):
        return getattr(self, "saved", None)


class _GenerationStub:
    async def generate(self, *, job_id, input_metadata, stored_inputs):
        from src.domain.try_on import TryOnQualityReport, TryOnResult, TryOnResultImage, TryOnWorkflowType

        return TryOnResult(
            job_id=job_id,
            workflow_type=TryOnWorkflowType.TRY_ON,
            result_image=TryOnResultImage(
                kind="sandbox_placeholder",
                url="/images/shared/try-on-sandbox-result.webp",
                alt="Sandbox Try-On result preview",
            ),
            quality_report=TryOnQualityReport(verdict="pass", confidence=0.9, checks=[], limitations=[]),
            stylist_note="OK",
            input_metadata=input_metadata,
            completed_at=_utc_now(),
        )


class _FileStorageStub:
    async def save_upload(self, *, job_id, role, filename, content_type, payload, sha256_hex):
        return TryOnStoredInput(
            role=role,
            storage_backend="s3",
            uri=f"s3://bucket/{job_id}/{filename}",
            bucket_name="bucket",
            object_key=f"{job_id}/{filename}",
            object_name=f"{job_id}/{filename}",
            content_type=content_type,
            size_bytes=len(payload),
            sha256=sha256_hex,
        )


@pytest.mark.asyncio
async def test_try_on_records_charge_through_billing_core() -> None:
    repository = InMemoryBillingRepository()
    await repository.ensure_account(owner_id="user-1", owner_type="person", initial_credits=100)
    billing_service = BillingService(
        repository=repository,
        policy_resolver=BillingPolicyResolver(workflow_base_costs={"try_on": 12}),
    )
    service = TryOnWorkflowService(
        repository=_RepositoryStub(),
        generator=_GenerationStub(),
        file_storage=_FileStorageStub(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/png"},
            max_upload_bytes=1024 * 1024,
        ),
        billing_service=billing_service,
        billing_owner_id="user-1",
        billing_owner_type=BillingOwnerType.PERSON,
    )

    accepted = await service.create_job(
        UploadFile(filename="human.png", file=__import__("io").BytesIO(b"human"), headers={"content-type": "image/png"}),
        UploadFile(filename="garment.png", file=__import__("io").BytesIO(b"garment"), headers={"content-type": "image/png"}),
    )
    job = await service.execute_job(job_id=accepted.job_id, lifecycle_mode=TryOnSandboxLifecycleMode.COMPLETE)

    assert job.cost_events[0].charged_credits == 12
    assert job.cost_events[0].charge_status == TryOnChargeStatus.CHARGED
