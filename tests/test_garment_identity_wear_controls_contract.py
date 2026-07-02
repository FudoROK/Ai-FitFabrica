from __future__ import annotations

import pytest

from src.adapters.agents.try_on_garment_identity_analysis import TryOnGarmentIdentityAnalysisAdapter
from src.adk_agents.garment_identity_agent.contracts import (
    GarmentIdentityContract,
    GarmentWearControlCandidate,
    UnknownGarmentTaxonomyCandidate,
)
from src.domain.agent_runtime import AgentInvocationEnvelope, AgentRuntimeStatus, AgentValidationStatus
from src.domain.try_on import TryOnStoredInput, TryOnUploadRole


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

    async def invoke(self, *, request, output_contract):
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


class _TaxonomyService:
    def __init__(self) -> None:
        self.captured_unknown_inputs: list[object] = []
        self.filtered_control_codes: list[str] = []

    async def resolve_available_controls(self, *, garment_type, unknown_input=None):
        if unknown_input is not None:
            self.captured_unknown_inputs.append(unknown_input)
        return object()

    async def filter_agent_control_candidates(self, *, garment_type, proposed_control_codes):
        self.filtered_control_codes = list(proposed_control_codes)

        class _Control:
            def __init__(self, control_code: str) -> None:
                self.control_code = control_code

        return [_Control("untucked")]


def test_garment_identity_contract_supports_wear_control_candidates() -> None:
    contract = GarmentIdentityContract(
        garment_type="relaxed shirt",
        taxonomy_parent="tops",
        taxonomy_confidence=0.87,
        wear_control_candidates=[
            GarmentWearControlCandidate(
                control_code="untucked",
                recommended=True,
                confidence=0.84,
                reason="Relaxed hip-length shirt is visually suitable for untucked wear.",
            )
        ],
        unknown_taxonomy_candidate=None,
        garment_count=1,
        target_garment_index=1,
        garment_visibility="fully_visible",
        crop_quality="full_garment",
        try_on_garment_coverage="sufficient",
        product_card_coverage="sufficient",
        occlusion_risk="low",
        required_regions_missing=[],
        ambiguous_target=False,
        dominant_color="blue",
        silhouette_summary="Relaxed long-sleeve shirt.",
        confidence=0.92,
        uncertainty_level="low",
    )

    assert contract.taxonomy_parent == "tops"
    assert contract.wear_control_candidates[0].control_code == "untucked"
    assert contract.wear_control_candidates[0].recommended is True


def test_garment_identity_contract_supports_unknown_taxonomy_candidate() -> None:
    contract = GarmentIdentityContract(
        garment_type="kimono jacket",
        taxonomy_parent=None,
        taxonomy_confidence=0.46,
        wear_control_candidates=[],
        unknown_taxonomy_candidate=UnknownGarmentTaxonomyCandidate(
            proposed_code="kimono jacket",
            proposed_display_name="Kimono jacket",
            proposed_category="outerwear",
            proposed_controls=["open", "draped"],
            confidence=0.74,
            agent_reasoning_summary="Looks like a lightweight open outerwear layer.",
        ),
        garment_count=1,
        target_garment_index=1,
        garment_visibility="fully_visible",
        crop_quality="full_garment",
        try_on_garment_coverage="sufficient",
        product_card_coverage="sufficient",
        occlusion_risk="low",
        required_regions_missing=[],
        ambiguous_target=False,
        dominant_color="beige",
        silhouette_summary="Open outerwear layer.",
        confidence=0.88,
        uncertainty_level="low",
    )

    assert contract.unknown_taxonomy_candidate is not None
    assert contract.unknown_taxonomy_candidate.proposed_code == "kimono jacket"


@pytest.mark.asyncio
async def test_try_on_garment_adapter_persists_wear_control_fields() -> None:
    service = _InvocationService(
        {
            "garment_type": "relaxed shirt",
            "taxonomy_parent": "tops",
            "taxonomy_confidence": 0.87,
            "wear_control_candidates": [
                {
                    "control_code": "untucked",
                    "recommended": True,
                    "confidence": 0.84,
                    "reason": "Relaxed shirt works best untucked.",
                }
            ],
            "unknown_taxonomy_candidate": None,
            "garment_count": 1,
            "target_garment_index": 1,
            "garment_visibility": "fully_visible",
            "crop_quality": "full_garment",
            "try_on_garment_coverage": "sufficient",
            "product_card_coverage": "sufficient",
            "occlusion_risk": "low",
            "required_regions_missing": [],
            "ambiguous_target": False,
            "dominant_color": "blue",
            "silhouette_summary": "Relaxed long-sleeve shirt.",
            "confidence": 0.92,
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

    assert result.taxonomy_parent == "tops"
    assert result.taxonomy_confidence == pytest.approx(0.87)
    assert result.wear_control_candidates[0]["control_code"] == "untucked"


@pytest.mark.asyncio
async def test_try_on_garment_adapter_filters_controls_and_captures_unknown_taxonomy() -> None:
    taxonomy_service = _TaxonomyService()
    service = _InvocationService(
        {
            "garment_type": "kimono jacket",
            "taxonomy_parent": None,
            "taxonomy_confidence": 0.46,
            "wear_control_candidates": [
                {
                    "control_code": "untucked",
                    "recommended": True,
                    "confidence": 0.84,
                    "reason": "Approved option.",
                },
                {
                    "control_code": "magic_style",
                    "recommended": False,
                    "confidence": 0.44,
                    "reason": "Not approved by backend catalog.",
                },
            ],
            "unknown_taxonomy_candidate": {
                "proposed_code": "kimono jacket",
                "proposed_display_name": "Kimono jacket",
                "proposed_category": "outerwear",
                "proposed_controls": ["open", "draped"],
                "confidence": 0.74,
                "agent_reasoning_summary": "Looks like a lightweight open outerwear layer.",
            },
            "garment_count": 1,
            "target_garment_index": 1,
            "garment_visibility": "fully_visible",
            "crop_quality": "full_garment",
            "try_on_garment_coverage": "sufficient",
            "product_card_coverage": "sufficient",
            "occlusion_risk": "low",
            "required_regions_missing": [],
            "ambiguous_target": False,
            "dominant_color": "beige",
            "silhouette_summary": "Open outerwear layer.",
            "confidence": 0.88,
            "uncertainty_level": "low",
        }
    )
    adapter = TryOnGarmentIdentityAnalysisAdapter(
        invocation_service=service,
        minimum_confidence=0.8,
        timeout_seconds=60,
        preferred_model=None,
        taxonomy_service=taxonomy_service,
    )

    result = await adapter.analyze(job_id="job-unknown", stored_inputs=[_garment_input()])

    assert taxonomy_service.filtered_control_codes == ["untucked", "magic_style"]
    assert len(taxonomy_service.captured_unknown_inputs) == 1
    assert result.wear_control_candidates == [
        {
            "control_code": "untucked",
            "recommended": True,
            "confidence": 0.84,
            "reason": "Approved option.",
            "risk": None,
        }
    ]
    assert result.unknown_taxonomy_candidate is not None
    assert result.unknown_taxonomy_candidate["proposed_code"] == "kimono jacket"
