from __future__ import annotations

from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import (
    TryOnChargeStatus,
    TryOnErrorCode,
    TryOnGenerationMode,
    TryOnJobStatus,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnSandboxLifecycleMode,
)
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from tests.try_on_human_identity_stub import AllowingHumanIdentityAnalysisStub
from tests.try_on_analysis_bundle_stub import required_analysis_bundle
from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter


def _upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), headers={"content-type": content_type})


@pytest.mark.anyio
async def test_try_on_workflow_service_persists_portable_job_state() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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


class _HandsRejectingQualityVerifier:
    """Verifier stub that simulates a blocking hand/anatomy defect."""

    async def verify(self, **_kwargs) -> TryOnQualityReport:
        return TryOnQualityReport(
            verdict="reject",
            confidence=0.9,
            checks=[
                TryOnQualityCheck(
                    name="visual_defect_hands",
                    status="failed",
                    confidence=1.0,
                    message="Generated image has severe malformed hands and extra fingers.",
                )
            ],
            limitations=["Blocking visual generation defect."],
        )


class _RetryThenPassQualityVerifier:
    """Verifier stub that asks for one retry and then accepts the retried result."""

    def __init__(self) -> None:
        self.calls = 0

    async def verify(self, **_kwargs) -> TryOnQualityReport:
        self.calls += 1
        if self.calls == 1:
            return TryOnQualityReport(
                verdict="reject",
                confidence=0.9,
                checks=[
                    TryOnQualityCheck(
                        name="visual_defect_hands",
                        status="failed",
                        confidence=1.0,
                        message="Generated image has severe malformed hands and extra fingers.",
                    )
                ],
                limitations=["Blocking visual generation defect."],
            )
        return TryOnQualityReport(
            verdict="pass",
            confidence=0.92,
            checks=[
                TryOnQualityCheck(
                    name="retry_quality_ok",
                    status="passed",
                    confidence=0.92,
                    message="Retried result passed quality verification.",
                )
            ],
            limitations=[],
        )


class _IdentityRejectingQualityVerifier:
    """Verifier stub that simulates a changed identity, which must not retry."""

    async def verify(self, **_kwargs) -> TryOnQualityReport:
        return TryOnQualityReport(
            verdict="reject",
            confidence=0.95,
            checks=[
                TryOnQualityCheck(
                    name="face_preservation",
                    status="failed",
                    confidence=0.95,
                    message="Face identity changed compared with the input.",
                )
            ],
            limitations=["Identity changed."],
        )


@pytest.mark.anyio
async def test_try_on_workflow_service_fails_when_quality_verifier_rejects_result() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
    assert failed.error.details["quality_confidence"] == 0.12
    assert failed.error.details["quality_limitations"] == ["Rejected in test."]
    assert failed.error.details["quality_checks"] == [
        {
            "name": "quality_reject",
            "status": "failed",
            "confidence": 0.12,
            "message": "Generated artifact failed deterministic verification.",
        }
    ]


@pytest.mark.anyio
async def test_try_on_workflow_service_labels_vertex_quality_rejection_cost_event() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=_VertexGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
    assert failed.cost_events[0].event_type == "try_on_vertex_virtual_try_on_generation"
    assert failed.cost_events[0].estimated_units == 1
    assert failed.cost_events[0].charge_status == TryOnChargeStatus.NOT_CHARGED
    assert failed.cost_events[0].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_workflow_service_records_retry_decision_for_blocking_hand_artifact() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=_VertexGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        quality_verifier=_HandsRejectingQualityVerifier(),
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
    assert failed.error.details["quality_decision"] == {
        "action": "retry_recommended",
        "reasons": ["blocking_generation_artifact"],
        "retry_categories": ["hands", "severe_artifact"],
    }
    assert failed.cost_events[0].event_type == "try_on_vertex_virtual_try_on_generation"
    assert failed.cost_events[0].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_workflow_service_auto_retries_once_for_retry_recommended_quality_failure() -> None:
    repository = InMemoryTryOnJobRepository()
    generator = _RecordingVertexGenerationAdapter()
    verifier = _RetryThenPassQualityVerifier()
    service = TryOnWorkflowService(
        repository=repository,
        generator=generator,
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        quality_verifier=verifier,
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
    assert generator.calls == 2
    assert verifier.calls == 2
    assert [event.stage for event in completed.status_history].count("vertex_virtual_try_on_generation") == 2
    assert completed.cost_events[0].event_type == "try_on_vertex_virtual_try_on_generation"
    assert completed.cost_events[0].estimated_units == 2
    assert completed.cost_events[0].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_workflow_service_stops_after_one_retry_recommended_quality_failure() -> None:
    repository = InMemoryTryOnJobRepository()
    generator = _RecordingVertexGenerationAdapter()
    service = TryOnWorkflowService(
        repository=repository,
        generator=generator,
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        quality_verifier=_HandsRejectingQualityVerifier(),
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
    assert generator.calls == 2
    assert failed.error is not None
    assert failed.error.details["retry_attempts"] == 1
    assert failed.error.details["quality_decision"]["action"] == "retry_recommended"
    assert failed.cost_events[0].estimated_units == 2
    assert failed.cost_events[0].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_workflow_service_does_not_retry_identity_rejection() -> None:
    repository = InMemoryTryOnJobRepository()
    generator = _RecordingVertexGenerationAdapter()
    service = TryOnWorkflowService(
        repository=repository,
        generator=generator,
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        quality_verifier=_IdentityRejectingQualityVerifier(),
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
    assert generator.calls == 1
    assert failed.error is not None
    assert failed.error.details["quality_decision"]["action"] == "reject"
    assert failed.error.details["retry_attempts"] == 0
    assert failed.cost_events[0].estimated_units == 1


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


class _RepairRecommendedThenFailIfReverifiedVerifier:
    """Verifier stub that proves blocked repair results are not reverified again."""

    def __init__(self) -> None:
        self.calls = 0

    async def verify(self, **kwargs) -> TryOnQualityReport:
        self.calls += 1
        if self.calls > 1:
            raise AssertionError("blocked repair result must not be reverified")
        return TryOnQualityReport(
            verdict="repair_recommended",
            confidence=0.7,
            checks=[
                TryOnQualityCheck(
                    name="minor_pose_artifact",
                    status="warning",
                    confidence=0.7,
                    message="Local pose artifact could be repaired.",
                )
            ],
            limitations=["Repair first."],
        )


class _RepairAdapterStub:
    """Repair stub that marks the result as repaired."""

    def __init__(self) -> None:
        self.calls = 0

    async def repair(self, **kwargs):
        self.calls += 1
        result = kwargs["result"]
        return result.model_copy(update={"stylist_note": f"{result.stylist_note} repaired"})


class _BlockingRepairAdapterStub:
    """Repair adapter stub that fails closed before producing a repaired image."""

    def __init__(self) -> None:
        self.calls = 0

    async def repair(self, **kwargs):
        self.calls += 1
        result = kwargs["result"]
        quality_report = kwargs["quality_report"]
        return result.model_copy(
            update={
                "quality_report": TryOnQualityReport(
                    verdict="reject",
                    confidence=quality_report.confidence,
                    checks=list(quality_report.checks)
                    + [
                        TryOnQualityCheck(
                            name="repair_provider_not_production_ready",
                            status="failed",
                            confidence=1.0,
                            message="Configured repair provider is not production-ready for real generation.",
                        )
                    ],
                    limitations=list(quality_report.limitations),
                )
            }
        )


class _StylistAdapterStub:
    """Stylist stub that replaces the final user-facing explanation."""

    def __init__(self, note: str) -> None:
        self.note = note
        self.calls = 0

    async def generate_note(self, **kwargs) -> str:
        self.calls += 1
        return self.note


class _FailingGenerationAdapter:
    """Generation stub that simulates a provider/runtime outage."""

    generation_mode = TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON

    async def generate(self, **_kwargs):
        raise RuntimeError("provider secret outage details")


class _VertexGenerationAdapter(FakeTryOnGenerationAdapter):
    """Generation stub that behaves like a successful real Vertex adapter."""

    generation_mode = TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON


class _RecordingVertexGenerationAdapter(_VertexGenerationAdapter):
    """Generation stub that counts generation attempts."""

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, **kwargs):
        self.calls += 1
        return await super().generate(**kwargs)


@pytest.mark.anyio
async def test_try_on_workflow_service_repairs_when_quality_verifier_recommends_it() -> None:
    repository = InMemoryTryOnJobRepository()
    verifier = _RepairRecommendedVerifier()
    repair_adapter = _RepairAdapterStub()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
        TryOnJobStatus.ANALYZING_HUMAN,
        TryOnJobStatus.GENERATING,
        TryOnJobStatus.QUALITY_CHECKING,
        TryOnJobStatus.REPAIRING,
        TryOnJobStatus.COMPLETED,
    ]
    assert repair_adapter.calls == 1
    assert verifier.calls == 2
    assert [event.event_type for event in completed.cost_events] == [
        "try_on_sandbox_generation",
        "try_on_provider_runtime_image_editing_repair",
    ]
    assert completed.cost_events[1].estimated_units == 1
    assert completed.cost_events[1].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_workflow_service_repair_acceptance_mode_forces_repair_cost_event() -> None:
    repository = InMemoryTryOnJobRepository()
    verifier = _RetryThenPassQualityVerifier()
    repair_adapter = _RepairAdapterStub()
    service = TryOnWorkflowService(
        repository=repository,
        generator=_VertexGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
    completed = await service.execute_job(
        job_id=job.job_id,
        lifecycle_mode=TryOnSandboxLifecycleMode.REPAIR_ACCEPTANCE,
    )

    assert completed.status == TryOnJobStatus.COMPLETED
    assert repair_adapter.calls == 1
    assert [event.event_type for event in completed.cost_events] == [
        "try_on_vertex_virtual_try_on_generation",
        "try_on_provider_runtime_image_editing_repair",
    ]
    assert completed.cost_events[1].estimated_units == 1


@pytest.mark.anyio
async def test_try_on_workflow_service_repair_acceptance_mode_completes_sandbox_flow() -> None:
    repository = InMemoryTryOnJobRepository()
    repair_adapter = _RepairAdapterStub()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        quality_verifier=None,
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
    completed = await service.execute_job(
        job_id=job.job_id,
        lifecycle_mode=TryOnSandboxLifecycleMode.REPAIR_ACCEPTANCE,
    )

    assert completed.status == TryOnJobStatus.COMPLETED
    assert repair_adapter.calls == 1
    assert completed.result is not None
    assert completed.result.quality_report.verdict == "pass"
    assert completed.result.quality_report.checks[0].name == "repair_acceptance_final_verification"
    assert [event.event_type for event in completed.cost_events] == [
        "try_on_sandbox_generation",
        "try_on_provider_runtime_image_editing_repair",
    ]


@pytest.mark.anyio
async def test_try_on_workflow_service_fails_closed_when_repair_adapter_blocks_without_reverification() -> None:
    repository = InMemoryTryOnJobRepository()
    verifier = _RepairRecommendedThenFailIfReverifiedVerifier()
    repair_adapter = _BlockingRepairAdapterStub()
    service = TryOnWorkflowService(
        repository=repository,
        generator=_VertexGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
    failed = await service.execute_job(job_id=job.job_id)

    assert failed.status == TryOnJobStatus.FAILED
    assert verifier.calls == 1
    assert repair_adapter.calls == 1
    assert failed.error is not None
    assert failed.error.details["quality_decision"]["action"] == "reject"
    assert any(
        check["name"] == "repair_provider_not_production_ready"
        for check in failed.error.details["quality_checks"]
    )
    assert [event.event_type for event in failed.cost_events] == [
        "try_on_vertex_virtual_try_on_generation",
        "try_on_provider_runtime_image_editing_repair",
    ]
    assert failed.cost_events[1].estimated_units == 1
    assert failed.cost_events[1].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_workflow_service_overrides_final_stylist_note_from_separate_stylist_step() -> None:
    repository = InMemoryTryOnJobRepository()
    stylist_adapter = _StylistAdapterStub(note="Отдельный stylist backend подготовил итоговое объяснение.")
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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


@pytest.mark.anyio
async def test_try_on_workflow_service_fails_closed_when_generation_adapter_raises() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=_FailingGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
    failed = await service.execute_job(job_id=job.job_id)

    assert failed.status == TryOnJobStatus.FAILED
    assert failed.error is not None
    assert failed.error.code == TryOnErrorCode.GENERATION_FAILED
    assert failed.error.details == {
        "job_id": job.job_id,
        "stage": "try_on_generation",
        "generation_mode": TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON.value,
    }
    assert "secret" not in failed.error.message
    assert failed.cost_events[0].event_type == "try_on_vertex_virtual_try_on_generation"
    assert failed.cost_events[0].estimated_units == 1
    assert failed.cost_events[0].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_workflow_service_labels_real_vertex_generation_without_sandbox_bookkeeping() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=_VertexGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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

    assert completed.status == TryOnJobStatus.COMPLETED
    assert completed.generation_mode == TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON
    assert [event.stage for event in completed.status_history] == [
        "accepted",
        "human_identity_analysis",
        "vertex_virtual_try_on_generation",
        "quality_check",
        "completed",
    ]
    assert completed.status_history[2].message == "Generating Vertex Virtual Try-On result."
    assert completed.status_history[-1].message == "Try-On job completed."
    assert completed.cost_events[0].event_type == "try_on_vertex_virtual_try_on_generation"
    assert completed.cost_events[0].estimated_units == 1
    assert completed.cost_events[0].charge_status == TryOnChargeStatus.NOT_CHARGED
