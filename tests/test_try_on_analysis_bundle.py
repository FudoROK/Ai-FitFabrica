from __future__ import annotations

import asyncio

import pytest

from src.domain.try_on import TryOnHumanIdentityAnalysis, TryOnHumanIdentityVerdict
from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.domain.try_on_analysis import (
    TryOnGarmentIdentityAnalysis,
    TryOnGarmentSlotIdentityAnalysis,
    TryOnMaterialTextureAnalysis,
)
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundleService
from src.use_cases.try_on.analysis_errors import TryOnAnalysisBundleFailure


def _human() -> TryOnHumanIdentityAnalysis:
    return TryOnHumanIdentityAnalysis(
        invocation_id="human-1",
        prompt_version="human.v1",
        contract_version="human.contract.v1",
        face_visibility="fully_visible",
        pose_summary="Front pose.",
        body_region_visibility=["face", "torso"],
        subject_count=1,
        crop_quality="full_body",
        try_on_body_coverage="sufficient",
        occlusion_risk="low",
        required_regions_missing=[],
        confidence=0.95,
        uncertainty_level="low",
        verdict=TryOnHumanIdentityVerdict.ALLOWED,
    )


def _garment() -> TryOnGarmentIdentityAnalysis:
    return TryOnGarmentIdentityAnalysis(
        invocation_id="garment-1",
        prompt_version="garment.v1",
        contract_version="garment.contract.v1",
        garment_type="coat",
        dominant_color="brown",
        silhouette_summary="Straight coat.",
        confidence=0.94,
        uncertainty_level="low",
    )


def _material() -> TryOnMaterialTextureAnalysis:
    return TryOnMaterialTextureAnalysis(
        invocation_id="material-1",
        prompt_version="material.v1",
        contract_version="material.contract.v1",
        evidence_note="Visible matte woven surface.",
        confidence=0.9,
        uncertainty_level="medium",
    )


class _Analyzer:
    def __init__(self, result, *, started: list[str], name: str, release: asyncio.Event) -> None:
        self._result = result
        self._started = started
        self._name = name
        self._release = release

    async def analyze(self, *, job_id, stored_inputs):
        self._started.append(self._name)
        await self._release.wait()
        return self._result


class _SlotRecordingGarmentAnalyzer:
    def __init__(self) -> None:
        self.calls: list[list[TryOnUploadRole]] = []

    async def analyze(self, *, job_id, stored_inputs):
        self.calls.append([item.role for item in stored_inputs])
        role = next(item.role for item in stored_inputs if item.role != TryOnUploadRole.HUMAN_PHOTO)
        return TryOnGarmentIdentityAnalysis(
            invocation_id=f"garment-{role.value}",
            prompt_version="garment.v1",
            contract_version="garment.contract.v1",
            garment_type=role.value,
            dominant_color="blue",
            silhouette_summary=f"{role.value} silhouette.",
            confidence=0.9,
            uncertainty_level="low",
        )


@pytest.mark.asyncio
async def test_analysis_bundle_runs_all_required_analyses_concurrently() -> None:
    started: list[str] = []
    release = asyncio.Event()
    service = TryOnAnalysisBundleService(
        human_identity_analyzer=_Analyzer(_human(), started=started, name="human", release=release),
        garment_identity_analyzer=_Analyzer(_garment(), started=started, name="garment", release=release),
        material_texture_analyzer=_Analyzer(_material(), started=started, name="material", release=release),
    )

    task = asyncio.create_task(
        service.analyze(
            job_id="job-1",
            stored_inputs=[_stored(TryOnUploadRole.GARMENT_PHOTO)],
        )
    )
    for _attempt in range(10):
        if len(started) == 3:
            break
        await asyncio.sleep(0)

    assert sorted(started) == ["garment", "human", "material"]
    release.set()
    bundle = await task
    assert bundle.human_identity.invocation_id == "human-1"
    assert bundle.garment_identity.invocation_id == "garment-1"
    assert bundle.material_texture.invocation_id == "material-1"


class _FailingAnalyzer:
    async def analyze(self, *, job_id, stored_inputs):
        raise RuntimeError("provider secret must not escape")


@pytest.mark.asyncio
async def test_analysis_bundle_fails_closed_without_exposing_provider_error() -> None:
    release = asyncio.Event()
    release.set()
    service = TryOnAnalysisBundleService(
        human_identity_analyzer=_Analyzer(_human(), started=[], name="human", release=release),
        garment_identity_analyzer=_FailingAnalyzer(),
        material_texture_analyzer=_Analyzer(_material(), started=[], name="material", release=release),
    )

    with pytest.raises(TryOnAnalysisBundleFailure) as exc_info:
        await service.analyze(job_id="job-1", stored_inputs=[])

    assert exc_info.value.safe_code == "required_try_on_analysis_failed"
    assert "secret" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_analysis_bundle_runs_garment_identity_per_outfit_slot() -> None:
    release = asyncio.Event()
    release.set()
    garment_analyzer = _SlotRecordingGarmentAnalyzer()
    service = TryOnAnalysisBundleService(
        human_identity_analyzer=_Analyzer(_human(), started=[], name="human", release=release),
        garment_identity_analyzer=garment_analyzer,
        material_texture_analyzer=_Analyzer(_material(), started=[], name="material", release=release),
    )

    bundle = await service.analyze(
        job_id="job-1",
        stored_inputs=[
            _stored(TryOnUploadRole.HUMAN_PHOTO),
            _stored(TryOnUploadRole.UPPER_GARMENT_PHOTO),
            _stored(TryOnUploadRole.LOWER_GARMENT_PHOTO),
        ],
    )

    assert [item.slot_role for item in bundle.garment_slot_analyses] == [
        "upper_garment_photo",
        "lower_garment_photo",
    ]
    assert bundle.garment_identity.garment_type == "upper_garment_photo"
    assert garment_analyzer.calls == [
        [TryOnUploadRole.UPPER_GARMENT_PHOTO],
        [TryOnUploadRole.LOWER_GARMENT_PHOTO],
    ]


def _stored(role: TryOnUploadRole) -> TryOnStoredInput:
    return TryOnStoredInput(
        role=role,
        storage_backend="s3",
        uri=f"s3://bucket/{role.value}.png",
        bucket_name="bucket",
        object_key=f"{role.value}.png",
        content_type="image/png",
        size_bytes=10,
        sha256="a" * 64,
    )
