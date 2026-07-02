from __future__ import annotations

import json

import pytest

from src.adapters.agents.adk_agent_gateway import AdkAgentGateway
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentProviderFailure
from src.llm.core.request import LLMArtifact
from src.llm.core.result import LLMResult
from src.llm.core.types import LLMError, Usage


class _AgentRuntimeStub:
    provider_name = "vertex"
    supports_artifacts = True

    def __init__(self, result: LLMResult) -> None:
        self.result = result
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.result


class _ArtifactResolverStub:
    def resolve(self, reference: AgentArtifactReference) -> LLMArtifact:
        return LLMArtifact(
            purpose=reference.purpose,
            content_type=reference.content_type,
            payload=b"real-image-bytes",
        )


class _TextOnlyAgentRuntimeStub(_AgentRuntimeStub):
    supports_artifacts = False


def _request() -> AgentInvocationRequest:
    return AgentInvocationRequest(
        agent_name="human_identity_agent",
        prompt_version="human_identity.v1",
        contract_version="human_identity.contract.v1",
        trace_id="trace-1",
        prompt="Analyze approved human image evidence.",
        input_payload={"human_photo_object_key": "private/person.jpg"},
        artifact_references=[
            AgentArtifactReference(
                purpose="human_photo",
                object_key="private/person.jpg",
                content_type="image/jpeg",
                size_bytes=16,
                sha256="a" * 64,
            )
        ],
        response_schema={"type": "object", "required": ["confidence"]},
        timeout_seconds=12,
        preferred_model="gemini-2.5-flash",
    )


@pytest.mark.asyncio
async def test_adk_agent_gateway_maps_backend_request_to_provider_runtime() -> None:
    runtime = _AgentRuntimeStub(
        LLMResult(
            status="ok",
            structured_data={"confidence": 0.9},
            provider="vertex",
            model="gemini-2.5-flash",
            latency_ms=25,
            usage=Usage(input_tokens=100, output_tokens=20, total_tokens=120),
        )
    )
    gateway = AdkAgentGateway(agent_runtime=runtime, artifact_resolver=_ArtifactResolverStub())

    result = await gateway.invoke(_request())

    assert result.payload == {"confidence": 0.9}
    assert result.cost_metadata == {"input_tokens": 100, "output_tokens": 20, "total_tokens": 120}
    provider_request = runtime.requests[0]
    assert provider_request.task == "human_identity_agent"
    assert provider_request.structured_output["required"] is True
    assert provider_request.structured_output["schema"] == {"type": "object", "required": ["confidence"]}
    assert provider_request.metadata["trace_id"] == "trace-1"
    assert json.loads(provider_request.input)["context"] == {"human_photo_object_key": "private/person.jpg"}
    assert provider_request.artifacts == [
        LLMArtifact(purpose="human_photo", content_type="image/jpeg", payload=b"real-image-bytes")
    ]


@pytest.mark.asyncio
async def test_adk_agent_gateway_fails_closed_when_artifact_resolver_is_missing() -> None:
    gateway = AdkAgentGateway(
        agent_runtime=_AgentRuntimeStub(LLMResult(status="ok", structured_data={"confidence": 0.9}))
    )

    with pytest.raises(AgentProviderFailure) as exc_info:
        await gateway.invoke(_request())

    assert exc_info.value.code == "artifact_resolution_failed"


@pytest.mark.asyncio
async def test_adk_agent_gateway_fails_closed_when_runtime_cannot_inspect_artifacts() -> None:
    gateway = AdkAgentGateway(
        agent_runtime=_TextOnlyAgentRuntimeStub(
            LLMResult(status="ok", structured_data={"confidence": 0.9})
        ),
        artifact_resolver=_ArtifactResolverStub(),
    )

    with pytest.raises(AgentProviderFailure) as exc_info:
        await gateway.invoke(_request())

    assert exc_info.value.code == "multimodal_runtime_required"


@pytest.mark.asyncio
async def test_adk_agent_gateway_rejects_missing_structured_provider_output() -> None:
    gateway = AdkAgentGateway(
        agent_runtime=_AgentRuntimeStub(
            LLMResult(
                status="ok",
                text="unstructured",
                structured_data=None,
                provider="vertex",
                model="gemini-2.5-flash",
                latency_ms=25,
            )
        ),
        artifact_resolver=_ArtifactResolverStub(),
    )

    with pytest.raises(AgentProviderFailure, match="structured output") as exc_info:
        await gateway.invoke(_request())

    assert exc_info.value.code == "invalid_output"
    assert exc_info.value.retriable is False


@pytest.mark.asyncio
async def test_adk_agent_gateway_preserves_safe_provider_failure_metadata() -> None:
    gateway = AdkAgentGateway(
        agent_runtime=_AgentRuntimeStub(
            LLMResult(
                status="error",
                provider="vertex",
                model="gemini-2.5-flash",
                latency_ms=25,
                error=LLMError(
                    type="rate_limited",
                    message_redacted="token=secret-value provider rate limited",
                    retriable=True,
                    http_status=429,
                ),
            )
        ),
        artifact_resolver=_ArtifactResolverStub(),
    )

    with pytest.raises(AgentProviderFailure) as exc_info:
        await gateway.invoke(_request())

    assert exc_info.value.code == "rate_limited"
    assert exc_info.value.retriable is True
    assert "secret-value" not in exc_info.value.message
