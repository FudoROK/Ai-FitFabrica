from __future__ import annotations

import pytest

from src.adapters.agents.product_card_generation import ProductCardAgentGenerationAdapter
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.domain.agent_runtime import (
    AgentInvocationEnvelope,
    AgentInvocationErrorDetail,
    AgentRuntimeStatus,
    AgentValidationStatus,
)
from src.domain.product_card import ProductCardGarmentAnalysis, ProductCardRequest
from src.use_cases.product_card.generation_errors import ProductCardGenerationFailure


class _InvocationServiceStub:
    def __init__(self, envelope: AgentInvocationEnvelope) -> None:
        self.envelope = envelope
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append((request, output_contract))
        return self.envelope


def _success_envelope() -> AgentInvocationEnvelope:
    return AgentInvocationEnvelope(
        invocation_id="invocation-product-card-1",
        trace_id="product_card_1",
        agent_name="product_card_agent",
        prompt_version="product_card.v1",
        contract_version="product_card.contract.v1",
        status=AgentRuntimeStatus.SUCCEEDED,
        validation_status=AgentValidationStatus.PASSED,
        output={
            "title": "Premium linen shirt",
            "short_description": "A clean marketplace-ready linen shirt description.",
            "key_attributes": ["linen texture", "relaxed fit"],
            "merchandising_notes": ["Use the front image as the hero image."],
            "confidence": 0.88,
            "limitations": ["Exact fiber composition is not confirmed."],
        },
        provider="replaceable-provider",
        model="provider-model",
        latency_ms=20,
        confidence=0.88,
    )


def _garment_analysis() -> ProductCardGarmentAnalysis:
    return ProductCardGarmentAnalysis(
        job_id="product_card_1",
        invocation_id="garment-invocation-1",
        prompt_version="garment_identity.v1",
        contract_version="garment_identity.contract.v1",
        garment_type="shirt",
        dominant_color="white",
        silhouette_summary="Relaxed shirt.",
        preserved_details=["point collar"],
        confidence=0.94,
        uncertainty_level="low",
    )


@pytest.mark.anyio
async def test_product_card_agent_adapter_maps_artifacts_and_structured_output() -> None:
    storage = InMemoryObjectStorage()
    payload = b"product-image"
    stored = storage.put_bytes(object_key="fitfabrica/public/product-card/source.png", payload=payload, content_type="image/png")
    invocation_service = _InvocationServiceStub(_success_envelope())
    adapter = ProductCardAgentGenerationAdapter(
        invocation_service=invocation_service,
        timeout_seconds=45,
        preferred_model=None,
    )

    draft = await adapter.generate(
        request=ProductCardRequest(
            title_hint="Linen shirt",
            category="shirt",
            target_channel="wildberries",
            brand_tone="premium editorial",
        ),
        garment_analysis=_garment_analysis(),
    )

    invocation, output_contract = invocation_service.requests[0]
    assert invocation.input_payload["category"] == "shirt"
    assert invocation.preferred_model is None
    assert invocation.artifact_references == []
    assert invocation.input_payload["garment_analysis"]["garment_type"] == "shirt"
    assert output_contract.__name__ == "ProductCardContentContract"
    assert draft.title == "Premium linen shirt"
    assert draft.bullet_points == ["linen texture", "relaxed fit"]
    assert draft.attributes["confidence"] == "0.88"


@pytest.mark.anyio
async def test_product_card_agent_adapter_maps_invocation_failure_to_safe_failure() -> None:
    storage = InMemoryObjectStorage()
    storage.put_bytes(object_key="source.png", payload=b"image", content_type="image/png")
    envelope = AgentInvocationEnvelope(
        invocation_id="invocation-product-card-2",
        trace_id="product_card_2",
        agent_name="product_card_agent",
        prompt_version="product_card.v1",
        contract_version="product_card.contract.v1",
        status=AgentRuntimeStatus.FAILED,
        validation_status=AgentValidationStatus.NOT_RUN,
        error=AgentInvocationErrorDetail(code="timeout", message="Agent invocation timed out.", retriable=True),
    )
    adapter = ProductCardAgentGenerationAdapter(
        invocation_service=_InvocationServiceStub(envelope),
        timeout_seconds=45,
        preferred_model=None,
    )

    with pytest.raises(ProductCardGenerationFailure) as exc_info:
        await adapter.generate(
            request=ProductCardRequest(
                title_hint="Linen shirt",
                category="shirt",
                target_channel="wildberries",
                brand_tone="premium editorial",
            ),
            garment_analysis=_garment_analysis(),
        )

    assert exc_info.value.safe_code == "timeout"
