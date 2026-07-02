from __future__ import annotations

from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import TryOnErrorCode, TryOnJobStatus
from src.use_cases.try_on.instruction_errors import TryOnInstructionFailure
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from tests.try_on_analysis_bundle_stub import required_analysis_bundle
from tests.try_on_human_identity_stub import AllowingHumanIdentityAnalysisStub


def _upload(name: str, payload: bytes) -> UploadFile:
    return UploadFile(filename=name, file=BytesIO(payload), headers={"content-type": "image/png"})


class _InstructionCreator:
    def __init__(self, result=None, failure: Exception | None = None) -> None:
        self.result = result
        self.failure = failure

    async def create(self, *, job_id, analysis_bundle, wear_control_selections=None):
        if self.failure is not None:
            raise self.failure
        return self.result


class _RecordingGenerator(FakeTryOnGenerationAdapter):
    def __init__(self) -> None:
        self.instructions = []

    async def generate(self, **kwargs):
        self.instructions.append(kwargs["instruction"])
        return await super().generate(**kwargs)


@pytest.mark.anyio
async def test_workflow_persists_instruction_and_passes_it_to_generation() -> None:
    from src.domain.try_on_instruction import TryOnGenerationInstruction

    instruction = TryOnGenerationInstruction(
        invocation_id="instruction-1",
        prompt_version="try_on.v1",
        contract_version="try_on.contract.v1",
        instruction_summary="Preserve approved identity and garment constraints.",
        confidence=0.95,
        uncertainty_level="low",
    )
    generator = _RecordingGenerator()
    service = TryOnWorkflowService(
        repository=InMemoryTryOnJobRepository(),
        generator=generator,
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=_InstructionCreator(result=instruction),
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(allowed_content_types={"image/png"}, max_upload_bytes=1024),
    )
    job = await service.create_job(human_photo=_upload("human.png", b"human"), garment_photo=_upload("garment.png", b"garment"))

    completed = await service.execute_job(job_id=job.job_id)

    assert completed.instruction == instruction
    assert generator.instructions == [instruction]


@pytest.mark.anyio
async def test_instruction_failure_blocks_generation_and_charging() -> None:
    generator = _RecordingGenerator()
    service = TryOnWorkflowService(
        repository=InMemoryTryOnJobRepository(),
        generator=generator,
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=_InstructionCreator(failure=TryOnInstructionFailure(safe_code="instruction_timeout")),
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(allowed_content_types={"image/png"}, max_upload_bytes=1024),
    )
    job = await service.create_job(human_photo=_upload("human.png", b"human"), garment_photo=_upload("garment.png", b"garment"))

    failed = await service.execute_job(job_id=job.job_id)

    assert failed.status == TryOnJobStatus.FAILED
    assert failed.error is not None
    assert failed.error.code == TryOnErrorCode.INSTRUCTION_GENERATION_FAILED
    assert failed.cost_events[0].charged_credits == 0
    assert generator.instructions == []
