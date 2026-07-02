"""Canonical backend service for invoking and validating product agents."""

from __future__ import annotations

import asyncio
from datetime import datetime
from decimal import Decimal
import logging
from time import perf_counter

from pydantic import BaseModel, ValidationError

from src.costs.provider_price_config import (
    COST_CONFIG_VERSION,
    estimate_internal_cost_usd,
    estimate_provider_cost_usd,
    get_provider_model_price,
)
from src.domain.agent_runtime import (
    AgentInvocationEnvelope,
    AgentInvocationErrorDetail,
    AgentInvocationRecord,
    AgentInvocationRequest,
    AgentProviderFailure,
    AgentProviderResult,
    AgentRuntimeStatus,
    AgentValidationStatus,
    utc_now,
)
from src.use_cases.agents.ports import AgentInvocationPort, AgentInvocationRepositoryPort
from src.utils.log_redaction import redact

logger = logging.getLogger(__name__)


class AgentInvocationService:
    """Invoke agents through one gateway and persist safe audit metadata."""

    def __init__(self, *, gateway: AgentInvocationPort, repository: AgentInvocationRepositoryPort) -> None:
        """Store the canonical gateway and audit repository."""

        self._gateway = gateway
        self._repository = repository

    async def invoke(
        self,
        *,
        request: AgentInvocationRequest,
        output_contract: type[BaseModel],
    ) -> AgentInvocationEnvelope:
        """Invoke one agent, validate its output, and persist the final audit record."""

        started_at = utc_now()
        started_tick = perf_counter()
        try:
            provider_result = await asyncio.wait_for(
                self._gateway.invoke(request),
                timeout=request.timeout_seconds,
            )
        except TimeoutError:
            logger.warning(
                "AGENT_INVOCATION_TIMEOUT",
                extra={"agent_name": request.agent_name, "trace_id": request.trace_id},
            )
            return await self._persist_failure(
                request=request,
                started_at=started_at,
                latency_ms=self._elapsed_ms(started_tick),
                validation_status=AgentValidationStatus.NOT_RUN,
                code="timeout",
                message="Agent invocation timed out.",
                retriable=True,
            )
        except AgentProviderFailure as exc:
            safe_message = redact(exc.message)[:500] or "Agent provider failed."
            logger.warning(
                "AGENT_INVOCATION_PROVIDER_FAILURE",
                extra={
                    "agent_name": request.agent_name,
                    "trace_id": request.trace_id,
                    "error_code": exc.code,
                    "retriable": exc.retriable,
                },
            )
            return await self._persist_failure(
                request=request,
                started_at=started_at,
                latency_ms=self._elapsed_ms(started_tick),
                validation_status=AgentValidationStatus.NOT_RUN,
                code=exc.code,
                message=safe_message,
                retriable=exc.retriable,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "AGENT_INVOCATION_UNEXPECTED_PROVIDER_FAILURE",
                extra={"agent_name": request.agent_name, "trace_id": request.trace_id},
            )
            return await self._persist_failure(
                request=request,
                started_at=started_at,
                latency_ms=self._elapsed_ms(started_tick),
                validation_status=AgentValidationStatus.NOT_RUN,
                code="provider_error",
                message=redact(exc)[:500] or "Agent provider failed.",
                retriable=False,
            )

        try:
            validated_output = output_contract.model_validate(provider_result.payload).model_dump(mode="json")
        except ValidationError:
            logger.warning(
                "AGENT_INVOCATION_CONTRACT_VALIDATION_FAILED",
                extra={"agent_name": request.agent_name, "trace_id": request.trace_id},
            )
            return await self._persist_failure(
                request=request,
                started_at=started_at,
                latency_ms=provider_result.latency_ms,
                validation_status=AgentValidationStatus.FAILED,
                code="invalid_output",
                message="Agent output failed backend contract validation.",
                retriable=False,
                provider_result=provider_result,
            )

        confidence = self._confidence_from(validated_output)
        cost_metadata = self._cost_metadata(
            request=request,
            provider=provider_result.provider,
            model=provider_result.model,
            latency_ms=provider_result.latency_ms,
            validation_status=AgentValidationStatus.PASSED.value,
            source_metadata=provider_result.cost_metadata,
        )
        envelope = AgentInvocationEnvelope(
            invocation_id=request.invocation_id,
            trace_id=request.trace_id,
            agent_name=request.agent_name,
            prompt_version=request.prompt_version,
            contract_version=request.contract_version,
            status=AgentRuntimeStatus.SUCCEEDED,
            validation_status=AgentValidationStatus.PASSED,
            output=validated_output,
            provider=provider_result.provider,
            model=provider_result.model,
            latency_ms=provider_result.latency_ms,
            confidence=confidence,
            cost_metadata=cost_metadata,
        )
        await self._repository.save(
            AgentInvocationRecord(
                invocation_id=request.invocation_id,
                trace_id=request.trace_id,
                agent_name=request.agent_name,
                prompt_version=request.prompt_version,
                contract_version=request.contract_version,
                provider=provider_result.provider,
                model=provider_result.model,
                status=envelope.status,
                validation_status=envelope.validation_status,
                latency_ms=provider_result.latency_ms,
                confidence=confidence,
                cost_metadata=cost_metadata,
                input_fields=sorted(request.input_payload),
                output_fields=sorted(validated_output),
                started_at=started_at,
                completed_at=utc_now(),
            )
        )
        return envelope

    async def _persist_failure(
        self,
        *,
        request: AgentInvocationRequest,
        started_at: datetime,
        latency_ms: int,
        validation_status: AgentValidationStatus,
        code: str,
        message: str,
        retriable: bool,
        provider_result: AgentProviderResult | None = None,
    ) -> AgentInvocationEnvelope:
        """Persist and return one safe typed invocation failure."""

        error = AgentInvocationErrorDetail(code=code, message=message, retriable=retriable)
        cost_metadata = self._cost_metadata(
            request=request,
            provider=provider_result.provider if provider_result else None,
            model=provider_result.model if provider_result else request.preferred_model,
            latency_ms=latency_ms,
            validation_status=validation_status.value,
            source_metadata=provider_result.cost_metadata if provider_result else {},
        )
        envelope = AgentInvocationEnvelope(
            invocation_id=request.invocation_id,
            trace_id=request.trace_id,
            agent_name=request.agent_name,
            prompt_version=request.prompt_version,
            contract_version=request.contract_version,
            status=AgentRuntimeStatus.FAILED,
            validation_status=validation_status,
            provider=provider_result.provider if provider_result else None,
            model=provider_result.model if provider_result else request.preferred_model,
            latency_ms=latency_ms,
            cost_metadata=cost_metadata,
            error=error,
        )
        await self._repository.save(
            AgentInvocationRecord(
                invocation_id=request.invocation_id,
                trace_id=request.trace_id,
                agent_name=request.agent_name,
                prompt_version=request.prompt_version,
                contract_version=request.contract_version,
                provider=envelope.provider,
                model=envelope.model,
                status=envelope.status,
                validation_status=validation_status,
                latency_ms=latency_ms,
                cost_metadata=cost_metadata,
                input_fields=sorted(request.input_payload),
                error_code=code,
                error_message=message,
                started_at=started_at,
                completed_at=utc_now(),
            )
        )
        return envelope

    @staticmethod
    def _confidence_from(output: dict[str, object]) -> float | None:
        """Return a valid numeric confidence value when the contract exposes one."""

        confidence = output.get("confidence")
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            return None
        return float(confidence)

    @staticmethod
    def _cost_metadata(
        *,
        request: AgentInvocationRequest,
        provider: str | None,
        model: str | None,
        latency_ms: int,
        validation_status: str,
        source_metadata: dict[str, object],
    ) -> dict[str, object]:
        """Return safe cost metadata for the agent invocation ledger."""

        input_tokens = _int_metadata(source_metadata, "input_tokens")
        output_tokens = _int_metadata(source_metadata, "output_tokens")
        image_input_count = _int_metadata(source_metadata, "image_input_count")
        image_output_count = _int_metadata(source_metadata, "image_output_count")
        generation_output_count = _int_metadata(source_metadata, "generation_output_count")
        usage_source = str(source_metadata.get("usage_source") or "estimated")
        metadata: dict[str, object] = {
            **source_metadata,
            "job_id": request.trace_id,
            "workflow_type": request.workflow_type or _infer_workflow_type(request.trace_id),
            "agent_name": request.agent_name,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "image_input_count": image_input_count,
            "image_output_count": image_output_count,
            "generation_output_count": generation_output_count,
            "attempt_number": request.attempt_number,
            "retry_reason": request.retry_reason,
            "repair_reason": request.repair_reason,
            "latency_ms": latency_ms,
            "validation_status": validation_status,
            "usage_source": usage_source,
            "cost_config_version": COST_CONFIG_VERSION,
        }
        if provider is None or model is None:
            metadata["estimated_provider_cost_usd"] = "0.000000"
            metadata["estimated_internal_cost_usd"] = "0.000000"
            metadata["cost_config_error"] = "provider_or_model_missing"
            return metadata
        try:
            price = get_provider_model_price(provider=provider, model=model)
            provider_cost = estimate_provider_cost_usd(
                price=price,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                image_inputs=image_input_count,
                image_outputs=image_output_count,
                image_generation_outputs=generation_output_count,
            )
            internal_cost = estimate_internal_cost_usd(provider_cost)
            metadata["estimated_provider_cost_usd"] = _decimal_string(provider_cost)
            metadata["estimated_internal_cost_usd"] = _decimal_string(internal_cost)
        except KeyError:
            metadata["estimated_provider_cost_usd"] = "0.000000"
            metadata["estimated_internal_cost_usd"] = "0.000000"
            metadata["cost_config_error"] = f"manual_price_config_required:{provider}/{model}"
        return metadata

    @staticmethod
    def _elapsed_ms(started_tick: float) -> int:
        """Return elapsed monotonic milliseconds."""

        return max(0, int((perf_counter() - started_tick) * 1000))


def _int_metadata(metadata: dict[str, object], key: str) -> int:
    """Return a non-negative integer from provider metadata."""

    value = metadata.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        return 0
    return max(0, value)


def _decimal_string(value: Decimal) -> str:
    """Return a JSON-safe fixed precision decimal string."""

    return f"{value:.6f}"


def _infer_workflow_type(trace_id: str) -> str:
    """Infer workflow type from current job id prefixes when request did not pass one."""

    known_prefixes = {
        "try_on_": "try_on",
        "product_card_": "product_card",
        "content_package_": "content_package",
        "pricing_": "pricing",
        "similar_search_": "similar_search",
        "outfit_": "outfit_recommendation",
    }
    for prefix, workflow_type in known_prefixes.items():
        if trace_id.startswith(prefix):
            return workflow_type
    return "unknown"
