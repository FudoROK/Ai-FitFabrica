from __future__ import annotations

import asyncio

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from src.domain.agent_runtime import (
    AgentInvocationRequest,
    AgentProviderFailure,
    AgentProviderResult,
    AgentRuntimeStatus,
    AgentValidationStatus,
)
from src.use_cases.agents.invocation_service import AgentInvocationService


class _OutputContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class _GatewayStub:
    def __init__(self, result: AgentProviderResult, *, delay_seconds: float = 0.0) -> None:
        self._result = result
        self._delay_seconds = delay_seconds

    async def invoke(self, request: AgentInvocationRequest) -> AgentProviderResult:
        if self._delay_seconds:
            await asyncio.sleep(self._delay_seconds)
        return self._result


class _RepositoryStub:
    def __init__(self) -> None:
        self.records = []

    async def save(self, record) -> None:
        self.records.append(record)


class _FailingGatewayStub:
    async def invoke(self, request: AgentInvocationRequest) -> AgentProviderResult:
        raise AgentProviderFailure(
            code="rate_limited",
            message="token=secret-value provider rate limited.",
            retriable=True,
        )


def _request(*, timeout_seconds: float = 2.0) -> AgentInvocationRequest:
    return AgentInvocationRequest(
        agent_name="human_identity_agent",
        prompt_version="human_identity.v1",
        contract_version="human_identity.contract.v1",
        trace_id="trace-1",
        prompt="Analyze approved artifacts.",
        input_payload={
            "human_photo_object_key": "private/person.jpg",
        },
        response_schema=_OutputContract.model_json_schema(),
        timeout_seconds=timeout_seconds,
    )


def _costed_request() -> AgentInvocationRequest:
    return AgentInvocationRequest(
        agent_name="human_identity_agent",
        prompt_version="human_identity.v1",
        contract_version="human_identity.contract.v1",
        trace_id="try_on_1",
        workflow_type="try_on",
        prompt="Analyze approved artifacts.",
        input_payload={
            "human_photo_object_key": "private/person.jpg",
        },
        response_schema=_OutputContract.model_json_schema(),
    )


@pytest.mark.asyncio
async def test_agent_invocation_service_validates_output_and_persists_safe_audit_record() -> None:
    repository = _RepositoryStub()
    service = AgentInvocationService(
        gateway=_GatewayStub(
            AgentProviderResult(
                payload={"summary": "Preserve visible face and pose.", "confidence": 0.91},
                provider="vertex",
                model="gemini-2.5-flash",
                latency_ms=42,
                cost_metadata={"input_tokens": 120, "output_tokens": 30},
            )
        ),
        repository=repository,
    )

    result = await service.invoke(request=_request(), output_contract=_OutputContract)

    assert result.status is AgentRuntimeStatus.SUCCEEDED
    assert result.validation_status is AgentValidationStatus.PASSED
    assert result.output == {"summary": "Preserve visible face and pose.", "confidence": 0.91}
    assert result.confidence == pytest.approx(0.91)
    assert len(repository.records) == 1
    record = repository.records[0]
    assert record.input_fields == ["human_photo_object_key"]
    assert record.output_fields == ["confidence", "summary"]
    assert not hasattr(record, "prompt")
    assert not hasattr(record, "input_payload")
    assert not hasattr(record, "output")


@pytest.mark.asyncio
async def test_agent_invocation_service_enriches_cost_metadata() -> None:
    repository = _RepositoryStub()
    service = AgentInvocationService(
        gateway=_GatewayStub(
            AgentProviderResult(
                payload={"summary": "Preserve visible face and pose.", "confidence": 0.91},
                provider="gemini",
                model="gemini-2.5-flash",
                latency_ms=42,
                cost_metadata={"input_tokens": 1_000_000, "output_tokens": 100_000, "usage_source": "provider_reported"},
            )
        ),
        repository=repository,
    )

    result = await service.invoke(request=_costed_request(), output_contract=_OutputContract)

    assert result.cost_metadata["job_id"] == "try_on_1"
    assert result.cost_metadata["workflow_type"] == "try_on"
    assert result.cost_metadata["provider"] == "gemini"
    assert result.cost_metadata["model"] == "gemini-2.5-flash"
    assert result.cost_metadata["estimated_provider_cost_usd"] == "0.550000"
    assert result.cost_metadata["estimated_internal_cost_usd"] == "0.660000"
    assert result.cost_metadata["cost_config_version"] == "provider_prices.gemini.2026-06-16.v1"
    assert repository.records[0].cost_metadata == result.cost_metadata


@pytest.mark.asyncio
async def test_agent_invocation_service_maps_invalid_output_to_typed_failure() -> None:
    repository = _RepositoryStub()
    service = AgentInvocationService(
        gateway=_GatewayStub(
            AgentProviderResult(
                payload={"summary": "Missing confidence"},
                provider="vertex",
                model="gemini-2.5-flash",
                latency_ms=10,
            )
        ),
        repository=repository,
    )

    result = await service.invoke(request=_request(), output_contract=_OutputContract)

    assert result.status is AgentRuntimeStatus.FAILED
    assert result.validation_status is AgentValidationStatus.FAILED
    assert result.error is not None
    assert result.error.code == "invalid_output"
    assert repository.records[0].error_code == "invalid_output"


@pytest.mark.asyncio
async def test_agent_invocation_service_enforces_timeout_and_persists_failure() -> None:
    repository = _RepositoryStub()
    service = AgentInvocationService(
        gateway=_GatewayStub(
            AgentProviderResult(
                payload={"summary": "Too late", "confidence": 0.8},
                provider="vertex",
                model="gemini-2.5-flash",
                latency_ms=500,
            ),
            delay_seconds=0.05,
        ),
        repository=repository,
    )

    result = await service.invoke(request=_request(timeout_seconds=0.01), output_contract=_OutputContract)

    assert result.status is AgentRuntimeStatus.FAILED
    assert result.validation_status is AgentValidationStatus.NOT_RUN
    assert result.error is not None
    assert result.error.code == "timeout"
    assert repository.records[0].error_message == "Agent invocation timed out."


@pytest.mark.asyncio
async def test_agent_invocation_service_preserves_typed_provider_failure() -> None:
    repository = _RepositoryStub()
    service = AgentInvocationService(gateway=_FailingGatewayStub(), repository=repository)

    result = await service.invoke(request=_request(), output_contract=_OutputContract)

    assert result.status is AgentRuntimeStatus.FAILED
    assert result.error is not None
    assert result.error.code == "rate_limited"
    assert result.error.retriable is True
    assert "secret-value" not in result.error.message
    assert repository.records[0].error_code == "rate_limited"
    assert "secret-value" not in repository.records[0].error_message


@pytest.mark.parametrize(
    "input_payload",
    [
        {"authorization": "Bearer secret-value"},
        {"nested": {"api_key": "secret-value"}},
        {"raw_image": b"binary-image-data"},
    ],
)
def test_agent_invocation_request_rejects_secrets_and_binary_payloads(input_payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        AgentInvocationRequest(
            agent_name="human_identity_agent",
            prompt_version="human_identity.v1",
            contract_version="human_identity.contract.v1",
            trace_id="trace-1",
            prompt="Analyze approved artifacts.",
            input_payload=input_payload,
            response_schema=_OutputContract.model_json_schema(),
        )
