from __future__ import annotations

import pytest

from src.adapters.agents.try_on_garment_identity_analysis import TryOnGarmentIdentityAnalysisAdapter
from src.adapters.agents.try_on_material_texture_analysis import TryOnMaterialTextureAnalysisAdapter
from src.domain.agent_runtime import AgentInvocationEnvelope, AgentRuntimeStatus, AgentValidationStatus
from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.analysis_errors import GarmentIdentityAnalysisFailure, MaterialTextureAnalysisFailure


def _garment_input() -> TryOnStoredInput:
    return TryOnStoredInput(
        role=TryOnUploadRole.GARMENT_PHOTO,
        storage_backend="s3",
        uri="s3://bucket/garment.webp",
        bucket_name="bucket",
        object_key="garment.webp",
        content_type="image/webp",
        size_bytes=3,
        sha256="a" * 64,
    )


class _InvocationService:
    def __init__(self, output: dict[str, object]) -> None:
        self.output = output
        self.request = None

    async def invoke(self, *, request, output_contract):
        self.request = request
        return AgentInvocationEnvelope(
            invocation_id="invocation-1",
            agent_name=request.agent_name,
            prompt_version=request.prompt_version,
            contract_version=request.contract_version,
            trace_id=request.trace_id,
            status=AgentRuntimeStatus.SUCCEEDED,
            validation_status=AgentValidationStatus.PASSED,
            output=self.output,
        )


@pytest.mark.asyncio
async def test_try_on_garment_adapter_maps_validated_agent_output() -> None:
    service = _InvocationService(
        {
            "garment_type": "coat",
            "garment_count": 1,
            "target_garment_index": 1,
            "target_garment_description": "brown straight coat",
            "garment_visibility": "fully_visible",
            "crop_quality": "full_garment",
            "try_on_garment_coverage": "sufficient",
            "product_card_coverage": "sufficient",
            "occlusion_risk": "low",
            "required_regions_missing": [],
            "ambiguous_target": False,
            "dominant_color": "brown",
            "silhouette_summary": "Straight coat.",
            "confidence": 0.95,
            "uncertainty_level": "low",
        }
    )
    adapter = TryOnGarmentIdentityAnalysisAdapter(
        invocation_service=service,
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    result = await adapter.analyze(job_id="job-1", stored_inputs=[_garment_input()])

    assert result.garment_type == "coat"
    assert service.request.artifact_references[0].object_key == "garment.webp"


@pytest.mark.asyncio
async def test_try_on_garment_adapter_fails_closed_on_low_confidence() -> None:
    service = _InvocationService(
        {
            "garment_type": "coat",
            "garment_count": 1,
            "garment_visibility": "fully_visible",
            "crop_quality": "full_garment",
            "try_on_garment_coverage": "sufficient",
            "product_card_coverage": "sufficient",
            "occlusion_risk": "low",
            "required_regions_missing": [],
            "ambiguous_target": False,
            "dominant_color": "brown",
            "silhouette_summary": "Straight coat.",
            "confidence": 0.2,
            "uncertainty_level": "low",
        }
    )
    adapter = TryOnGarmentIdentityAnalysisAdapter(
        invocation_service=service,
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    with pytest.raises(GarmentIdentityAnalysisFailure):
        await adapter.analyze(job_id="job-1", stored_inputs=[_garment_input()])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("output_overrides", "safe_code"),
    [
        ({"garment_count": 0}, "no_garment_detected"),
        ({"garment_count": 2, "ambiguous_target": True}, "multiple_garments_detected"),
        ({"try_on_garment_coverage": "partial"}, "insufficient_try_on_garment_coverage"),
        ({"occlusion_risk": "high"}, "garment_occlusion_risk_too_high"),
    ],
)
async def test_try_on_garment_adapter_blocks_false_passes(output_overrides: dict[str, object], safe_code: str) -> None:
    output: dict[str, object] = {
        "garment_type": "coat",
        "garment_count": 1,
        "target_garment_index": 1,
        "target_garment_description": "brown straight coat",
        "garment_visibility": "fully_visible",
        "crop_quality": "full_garment",
        "try_on_garment_coverage": "sufficient",
        "product_card_coverage": "sufficient",
        "occlusion_risk": "low",
        "required_regions_missing": [],
        "ambiguous_target": False,
        "dominant_color": "brown",
        "silhouette_summary": "Straight coat.",
        "confidence": 0.95,
        "uncertainty_level": "low",
    }
    output.update(output_overrides)
    service = _InvocationService(output)
    adapter = TryOnGarmentIdentityAnalysisAdapter(
        invocation_service=service,
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
    )

    with pytest.raises(GarmentIdentityAnalysisFailure) as exc_info:
        await adapter.analyze(job_id="job-1", stored_inputs=[_garment_input()])

    assert exc_info.value.safe_code == safe_code


@pytest.mark.asyncio
async def test_try_on_material_adapter_maps_honest_visual_output() -> None:
    service = _InvocationService(
        {
            "visible_material_signals": ["matte woven surface"],
            "texture_signals": ["fine weave"],
            "evidence_note": "Visible matte woven surface.",
            "confidence": 0.9,
            "composition_status": "unknown",
            "uncertainty_level": "medium",
            "observations": [{"signal_type": "finish", "observation": "matte finish is visible", "confidence": 0.9}],
            "evidence": [{"source_type": "artifact", "source_ref": "garment.webp", "observation": "matte surface", "confidence": 0.9}],
        }
    )
    adapter = TryOnMaterialTextureAnalysisAdapter(
        invocation_service=service,
        minimum_confidence=0.7,
        timeout_seconds=60,
        preferred_model=None,
    )

    result = await adapter.analyze(job_id="job-1", stored_inputs=[_garment_input()])

    assert result.composition_status == "unknown"
    assert service.request.agent_name == "material_texture_agent"


@pytest.mark.asyncio
async def test_try_on_material_adapter_fails_closed_on_high_uncertainty() -> None:
    service = _InvocationService(
        {
            "evidence_note": "Insufficient visible material evidence.",
            "confidence": 0.9,
            "composition_status": "unknown",
            "uncertainty_level": "high",
        }
    )
    adapter = TryOnMaterialTextureAnalysisAdapter(
        invocation_service=service,
        minimum_confidence=0.7,
        timeout_seconds=60,
        preferred_model=None,
    )

    with pytest.raises(MaterialTextureAnalysisFailure):
        await adapter.analyze(job_id="job-1", stored_inputs=[_garment_input()])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("output_overrides", "safe_code"),
    [
        (
            {"visible_material_signals": [], "texture_signals": [], "observations": []},
            "material_texture_visible_signals_missing",
        ),
        (
            {"visible_material_signals": ["matte surface"], "texture_signals": ["woven"], "observations": [], "evidence": []},
            "material_texture_evidence_missing",
        ),
        (
            {
                "visible_material_signals": ["matte surface"],
                "texture_signals": ["woven"],
                "composition_status": "trusted_fact_provided",
                "evidence": [{"source_type": "artifact", "source_ref": "garment.webp", "observation": "matte surface", "confidence": 0.9}],
            },
            "material_texture_invalid_output",
        ),
    ],
)
async def test_try_on_material_adapter_blocks_false_passes(output_overrides: dict[str, object], safe_code: str) -> None:
    output: dict[str, object] = {
        "visible_material_signals": ["matte woven surface"],
        "texture_signals": ["fine weave"],
        "evidence_note": "Visible matte woven surface.",
        "confidence": 0.9,
        "composition_status": "unknown",
        "uncertainty_level": "medium",
        "observations": [{"signal_type": "finish", "observation": "matte finish is visible", "confidence": 0.9}],
        "evidence": [{"source_type": "artifact", "source_ref": "garment.webp", "observation": "matte surface", "confidence": 0.9}],
        "alternative_interpretations": ["polyester blend or cotton blend cannot be distinguished visually"],
    }
    output.update(output_overrides)
    service = _InvocationService(output)
    adapter = TryOnMaterialTextureAnalysisAdapter(
        invocation_service=service,
        minimum_confidence=0.7,
        timeout_seconds=60,
        preferred_model=None,
    )

    with pytest.raises(MaterialTextureAnalysisFailure) as exc_info:
        await adapter.analyze(job_id="job-1", stored_inputs=[_garment_input()])

    assert exc_info.value.safe_code == safe_code
