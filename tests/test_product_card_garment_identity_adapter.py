from __future__ import annotations

from hashlib import sha256

import pytest

from src.adapters.agents.garment_identity_analysis import GarmentIdentityAnalysisAdapter
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.domain.agent_runtime import AgentInvocationEnvelope, AgentRuntimeStatus, AgentValidationStatus
from src.use_cases.product_card.garment_identity_errors import GarmentIdentityAnalysisFailure


class _InvocationServiceStub:
    def __init__(self, envelope: AgentInvocationEnvelope) -> None:
        self.envelope = envelope
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append((request, output_contract))
        return self.envelope


def _success_envelope(*, confidence: float = 0.95, uncertainty_level: str = "low") -> AgentInvocationEnvelope:
    return AgentInvocationEnvelope(
        invocation_id="garment-invocation-1",
        trace_id="product_card_1",
        agent_name="garment_identity_agent",
        prompt_version="garment_identity.v1",
        contract_version="garment_identity.contract.v2",
        status=AgentRuntimeStatus.SUCCEEDED,
        validation_status=AgentValidationStatus.PASSED,
        output={
            "garment_type": "coat",
            "garment_count": 1,
            "target_garment_index": 1,
            "target_garment_description": "khaki hooded coat",
            "garment_visibility": "fully_visible",
            "crop_quality": "full_garment",
            "try_on_garment_coverage": "sufficient",
            "product_card_coverage": "sufficient",
            "occlusion_risk": "low",
            "required_regions_missing": [],
            "ambiguous_target": False,
            "dominant_color": "khaki",
            "secondary_colors": ["brown"],
            "silhouette_summary": "Relaxed hooded coat.",
            "preserved_details": ["front buttons", "patch pockets"],
            "confidence": confidence,
            "limitations": [],
            "visual_details": [
                {"detail_type": "button", "description": "Front button closure.", "confidence": 0.97}
            ],
            "evidence": [
                {
                    "source_type": "artifact",
                    "source_ref": "product/source.webp",
                    "observation": "Button closure is visible.",
                    "confidence": 0.97,
                }
            ],
            "uncertainty_level": uncertainty_level,
            "unknowns": [],
        },
        provider="replaceable-provider",
        model="provider-model",
        latency_ms=20,
        confidence=confidence,
    )


@pytest.mark.anyio
async def test_garment_identity_adapter_maps_artifact_and_validated_output() -> None:
    storage = InMemoryObjectStorage()
    payload = b"garment-image"
    stored = storage.put_bytes(object_key="product/source.webp", payload=payload, content_type="image/webp")
    invocation_service = _InvocationServiceStub(_success_envelope())
    adapter = GarmentIdentityAnalysisAdapter(
        invocation_service=invocation_service,
        object_storage=storage,
        minimum_confidence=0.8,
        timeout_seconds=45,
        preferred_model=None,
    )

    analysis = await adapter.analyze(job_id="product_card_1", asset_keys=[stored.object_key])

    request, output_contract = invocation_service.requests[0]
    artifact = request.artifact_references[0]
    assert artifact.object_key == stored.object_key
    assert artifact.sha256 == sha256(payload).hexdigest()
    assert output_contract.__name__ == "GarmentIdentityContract"
    assert analysis.job_id == "product_card_1"
    assert analysis.garment_type == "coat"
    assert analysis.invocation_id == "garment-invocation-1"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("confidence", "uncertainty_level", "safe_code"),
    [(0.2, "low", "confidence_below_minimum"), (0.95, "high", "uncertainty_too_high")],
)
async def test_garment_identity_adapter_fails_closed_on_unsafe_analysis(
    confidence: float,
    uncertainty_level: str,
    safe_code: str,
) -> None:
    storage = InMemoryObjectStorage()
    storage.put_bytes(object_key="product/source.webp", payload=b"image", content_type="image/webp")
    adapter = GarmentIdentityAnalysisAdapter(
        invocation_service=_InvocationServiceStub(_success_envelope(confidence=confidence, uncertainty_level=uncertainty_level)),
        object_storage=storage,
        minimum_confidence=0.8,
        timeout_seconds=45,
        preferred_model=None,
    )

    with pytest.raises(GarmentIdentityAnalysisFailure) as exc_info:
        await adapter.analyze(job_id="product_card_1", asset_keys=["product/source.webp"])

    assert exc_info.value.safe_code == safe_code


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("output_overrides", "safe_code"),
    [
        ({"garment_count": 0}, "no_garment_detected"),
        ({"garment_count": 2, "ambiguous_target": True}, "multiple_garments_detected"),
        ({"crop_quality": "major_crop"}, "garment_crop_too_tight"),
        ({"product_card_coverage": "partial"}, "insufficient_product_card_coverage"),
    ],
)
async def test_garment_identity_adapter_blocks_product_card_false_passes(
    output_overrides: dict[str, object],
    safe_code: str,
) -> None:
    storage = InMemoryObjectStorage()
    storage.put_bytes(object_key="product/source.webp", payload=b"image", content_type="image/webp")
    envelope = _success_envelope()
    assert envelope.output is not None
    envelope.output.update(output_overrides)
    adapter = GarmentIdentityAnalysisAdapter(
        invocation_service=_InvocationServiceStub(envelope),
        object_storage=storage,
        minimum_confidence=0.8,
        timeout_seconds=45,
        preferred_model=None,
    )

    with pytest.raises(GarmentIdentityAnalysisFailure) as exc_info:
        await adapter.analyze(job_id="product_card_1", asset_keys=["product/source.webp"])

    assert exc_info.value.safe_code == safe_code
