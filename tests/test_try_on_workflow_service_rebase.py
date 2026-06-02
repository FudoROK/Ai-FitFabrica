from __future__ import annotations

from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import TryOnGenerationMode, TryOnJobStatus, TryOnQualityCheck, TryOnQualityReport
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService


def _upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), headers={"content-type": content_type})


@pytest.mark.anyio
async def test_try_on_workflow_service_persists_portable_job_state() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        quality_verifier=None,
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )

    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.webp", b"garment-image", "image/webp"),
    )
    completed = await service.execute_job(job_id=job.job_id)

    assert job.status == TryOnJobStatus.ACCEPTED
    assert completed.status == TryOnJobStatus.COMPLETED
    assert completed.generation_mode == TryOnGenerationMode.SANDBOX_FAKE
    assert completed.stored_inputs[0].storage_backend in {"in_memory", "s3"}


class _RejectingQualityVerifier:
    """Simple verifier stub that forces workflow rejection."""

    async def verify(self, **_kwargs) -> TryOnQualityReport:
        return TryOnQualityReport(
            verdict="reject",
            confidence=0.12,
            checks=[
                TryOnQualityCheck(
                    name="quality_reject",
                    status="failed",
                    confidence=0.12,
                    message="Generated artifact failed deterministic verification.",
                )
            ],
            limitations=["Rejected in test."],
        )


@pytest.mark.anyio
async def test_try_on_workflow_service_fails_when_quality_verifier_rejects_result() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        quality_verifier=_RejectingQualityVerifier(),
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )

    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.webp", b"garment-image", "image/webp"),
    )
    failed = await service.execute_job(job_id=job.job_id)

    assert failed.status == TryOnJobStatus.FAILED
    assert failed.error is not None
    assert failed.error.details["stage"] == "quality_verifier"


class _RepairRecommendedVerifier:
    """Verifier stub that asks the workflow to run repair first and pass after repair."""

    def __init__(self) -> None:
        self.calls = 0

    async def verify(self, **kwargs) -> TryOnQualityReport:
        self.calls += 1
        if self.calls == 1:
            return TryOnQualityReport(
                verdict="repair_recommended",
                confidence=0.5,
                checks=[
                    TryOnQualityCheck(
                        name="size_warning",
                        status="warning",
                        confidence=0.5,
                        message="Artifact is too small.",
                    )
                ],
                limitations=["Repair first."],
            )
        return TryOnQualityReport(
            verdict="pass",
            confidence=0.9,
            checks=[
                TryOnQualityCheck(
                    name="repair_ok",
                    status="passed",
                    confidence=0.9,
                    message="Repair completed.",
                )
            ],
            limitations=[],
        )


class _RepairAdapterStub:
    """Repair stub that marks the result as repaired."""

    def __init__(self) -> None:
        self.calls = 0

    async def repair(self, **kwargs):
        self.calls += 1
        result = kwargs["result"]
        return result.model_copy(update={"stylist_note": f"{result.stylist_note} repaired"})


class _StylistAdapterStub:
    """Stylist stub that replaces the final user-facing explanation."""

    def __init__(self, note: str) -> None:
        self.note = note
        self.calls = 0

    async def generate_note(self, **kwargs) -> str:
        self.calls += 1
        return self.note


@pytest.mark.anyio
async def test_try_on_workflow_service_repairs_when_quality_verifier_recommends_it() -> None:
    repository = InMemoryTryOnJobRepository()
    verifier = _RepairRecommendedVerifier()
    repair_adapter = _RepairAdapterStub()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        quality_verifier=verifier,
        repair_adapter=repair_adapter,
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )

    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.webp", b"garment-image", "image/webp"),
    )
    completed = await service.execute_job(job_id=job.job_id)

    assert completed.status == TryOnJobStatus.COMPLETED
    assert [event.status for event in completed.status_history] == [
        TryOnJobStatus.ACCEPTED,
        TryOnJobStatus.GENERATING,
        TryOnJobStatus.QUALITY_CHECKING,
        TryOnJobStatus.REPAIRING,
        TryOnJobStatus.COMPLETED,
    ]
    assert repair_adapter.calls == 1
    assert verifier.calls == 2


@pytest.mark.anyio
async def test_try_on_workflow_service_overrides_final_stylist_note_from_separate_stylist_step() -> None:
    repository = InMemoryTryOnJobRepository()
    stylist_adapter = _StylistAdapterStub(note="Отдельный stylist backend подготовил итоговое объяснение.")
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        quality_verifier=None,
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
        stylist_adapter=stylist_adapter,
    )

    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.webp", b"garment-image", "image/webp"),
    )
    completed = await service.execute_job(job_id=job.job_id)

    assert completed.status == TryOnJobStatus.COMPLETED
    assert completed.result is not None
    assert completed.result.stylist_note == "Отдельный stylist backend подготовил итоговое объяснение."
    assert stylist_adapter.calls == 1
