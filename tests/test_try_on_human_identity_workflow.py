from __future__ import annotations

from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import (
    TryOnErrorCode,
    TryOnHumanIdentityAnalysis,
    TryOnHumanIdentityPreservationTarget,
    TryOnHumanIdentityVerdict,
    TryOnJobStatus,
)
from src.domain.try_on_analysis import (
    TryOnGarmentIdentityAnalysis,
    TryOnGarmentSlotIdentityAnalysis,
    TryOnMaterialTextureAnalysis,
)
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundle
from src.use_cases.try_on.analysis_errors import TryOnAnalysisBundleFailure
from src.use_cases.try_on.human_identity_errors import HumanIdentityAnalysisFailure
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter


def _upload(filename: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(b"image-bytes"), headers={"content-type": "image/png"})


def _analysis(*, verdict: TryOnHumanIdentityVerdict = TryOnHumanIdentityVerdict.ALLOWED) -> TryOnHumanIdentityAnalysis:
    return TryOnHumanIdentityAnalysis(
        invocation_id="invocation-1",
        prompt_version="human_identity.v1",
        contract_version="human_identity.contract.v1",
        face_visibility="fully_visible",
        pose_summary="Front-facing pose.",
        body_region_visibility=["face", "torso", "arms", "legs"],
        subject_count=1,
        crop_quality="full_body",
        try_on_body_coverage="sufficient",
        occlusion_risk="low",
        required_regions_missing=[],
        preservation_targets=[
            TryOnHumanIdentityPreservationTarget(
                attribute_name="face",
                preservation_reason="Preserve visible identity.",
            )
        ],
        confidence=0.95,
        uncertainty_level="low",
        verdict=verdict,
        rejection_reasons=[] if verdict == TryOnHumanIdentityVerdict.ALLOWED else ["confidence_below_minimum"],
    )


class _AnalysisStub:
    def __init__(self, result: TryOnHumanIdentityAnalysis | Exception) -> None:
        self.result = result
        self.calls = 0

    async def analyze(self, **_kwargs) -> TryOnHumanIdentityAnalysis:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class _BundleStub:
    def __init__(self, human_result: TryOnHumanIdentityAnalysis | Exception) -> None:
        self.human_result = human_result

    async def analyze(self, **_kwargs) -> TryOnAnalysisBundle:
        if isinstance(self.human_result, Exception):
            raise self.human_result
        garment_identity = TryOnGarmentIdentityAnalysis(
            invocation_id="garment-1",
            prompt_version="garment.v1",
            contract_version="garment.contract.v1",
            garment_type="coat",
            dominant_color="brown",
            silhouette_summary="Straight coat.",
            confidence=0.95,
            uncertainty_level="low",
        )
        return TryOnAnalysisBundle(
            human_identity=self.human_result,
            garment_identity=garment_identity,
            garment_slot_analyses=[
                TryOnGarmentSlotIdentityAnalysis(slot_role="garment_photo", analysis=garment_identity)
            ],
            material_texture=TryOnMaterialTextureAnalysis(
                invocation_id="material-1",
                prompt_version="material.v1",
                contract_version="material.contract.v1",
                evidence_note="Visible matte woven surface.",
                confidence=0.9,
                uncertainty_level="medium",
            ),
        )


class _GenerationSpy(FakeTryOnGenerationAdapter):
    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, **kwargs):
        self.calls += 1
        return await super().generate(**kwargs)


def _service(analyzer: _AnalysisStub, generator: _GenerationSpy) -> TryOnWorkflowService:
    return TryOnWorkflowService(
        repository=InMemoryTryOnJobRepository(),
        generator=generator,
        analysis_bundle_service=_BundleStub(analyzer.result),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        quality_verifier=None,
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/png"},
            max_upload_bytes=1024,
        ),
    )


@pytest.mark.anyio
async def test_try_on_persists_human_identity_analysis_before_generation() -> None:
    generator = _GenerationSpy()
    service = _service(_AnalysisStub(_analysis()), generator)
    accepted = await service.create_job(human_photo=_upload("human.png"), garment_photo=_upload("garment.png"))

    completed = await service.execute_job(job_id=accepted.job_id)

    assert completed.status == TryOnJobStatus.COMPLETED
    assert completed.human_identity_analysis is not None
    assert completed.human_identity_analysis.invocation_id == "invocation-1"
    assert completed.garment_identity_analysis is not None
    assert completed.material_texture_analysis is not None
    assert generator.calls == 1
    assert TryOnJobStatus.ANALYZING_HUMAN in [event.status for event in completed.status_history]


@pytest.mark.anyio
async def test_try_on_blocks_generation_when_human_identity_analysis_fails() -> None:
    generator = _GenerationSpy()
    service = _service(_AnalysisStub(TryOnAnalysisBundleFailure()), generator)
    accepted = await service.create_job(human_photo=_upload("human.png"), garment_photo=_upload("garment.png"))

    failed = await service.execute_job(job_id=accepted.job_id)

    assert failed.status == TryOnJobStatus.FAILED
    assert failed.error is not None
    assert failed.error.code == TryOnErrorCode.REQUIRED_ANALYSIS_FAILED
    assert failed.cost_events[0].charged_credits == 0
    assert generator.calls == 0


@pytest.mark.anyio
async def test_try_on_blocks_generation_when_backend_policy_rejects_analysis() -> None:
    generator = _GenerationSpy()
    service = _service(_AnalysisStub(_analysis(verdict=TryOnHumanIdentityVerdict.BLOCKED)), generator)
    accepted = await service.create_job(human_photo=_upload("human.png"), garment_photo=_upload("garment.png"))

    failed = await service.execute_job(job_id=accepted.job_id)

    assert failed.status == TryOnJobStatus.FAILED
    assert failed.error is not None
    assert failed.error.code == TryOnErrorCode.HUMAN_IDENTITY_INPUT_NOT_SUITABLE
    assert failed.human_identity_analysis is not None
    assert generator.calls == 0
