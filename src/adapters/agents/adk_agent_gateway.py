"""Canonical gateway from backend agent requests to the configured agent runtime."""

from __future__ import annotations

import asyncio
import json

from src.domain.agent_runtime import AgentInvocationRequest, AgentProviderFailure, AgentProviderResult
from src.domain.provider_ports import AgentRuntimePort
from src.llm.core.request import LLMRequest
from src.llm.core.request import LLMArtifact
from src.llm.core.types import Usage
from src.use_cases.agents.ports import AgentArtifactResolverPort
from src.utils.log_redaction import redact


class AdkAgentGateway:
    """Invoke approved agents through the provider-neutral agent runtime port."""

    def __init__(
        self,
        *,
        agent_runtime: AgentRuntimePort,
        artifact_resolver: AgentArtifactResolverPort | None = None,
    ) -> None:
        """Store the configured provider runtime."""

        self._agent_runtime = agent_runtime
        self._artifact_resolver = artifact_resolver

    async def invoke(self, request: AgentInvocationRequest) -> AgentProviderResult:
        """Invoke one approved agent without exposing provider details to workflows."""

        artifacts = await self._resolve_artifacts(request)
        provider_request = LLMRequest(
            task=request.agent_name,
            input=json.dumps(
                {
                    "prompt": request.prompt,
                    "context": request.input_payload,
                },
                ensure_ascii=False,
            ),
            artifacts=artifacts,
            structured_output={
                "schema": request.response_schema,
                "required": True,
                "contract_version": request.contract_version,
            },
            model=request.preferred_model,
            metadata={
                "trace_id": request.trace_id,
                "invocation_id": request.invocation_id,
                "prompt_version": request.prompt_version,
                "contract_version": request.contract_version,
            },
            timeout_s=max(1, int(request.timeout_seconds)),
            max_retries=0,
        )
        result = await asyncio.to_thread(self._agent_runtime.generate, provider_request)
        if result.status != "ok":
            message = result.error.message_redacted if result.error is not None else "Agent provider failed."
            raise AgentProviderFailure(
                code=result.error.type if result.error is not None else "provider_error",
                message=redact(message)[:500] or "Agent provider failed.",
                retriable=result.error.retriable if result.error is not None else False,
            )
        if not isinstance(result.structured_data, dict):
            raise AgentProviderFailure(
                code="invalid_output",
                message="Agent provider did not return structured output.",
                retriable=False,
            )

        return AgentProviderResult(
            payload={str(key): value for key, value in result.structured_data.items()},
            provider=result.provider or self._agent_runtime.provider_name,
            model=result.model or request.preferred_model or "unknown",
            latency_ms=max(0, int(result.latency_ms or 0)),
            cost_metadata=self._cost_metadata(result.usage),
        )

    async def _resolve_artifacts(self, request: AgentInvocationRequest) -> list[LLMArtifact]:
        """Resolve approved references into transient provider inputs."""

        if not request.artifact_references:
            return []
        if not self._agent_runtime.supports_artifacts:
            raise AgentProviderFailure(
                code="multimodal_runtime_required",
                message="Configured agent runtime cannot inspect approved artifacts.",
                retriable=False,
            )
        if self._artifact_resolver is None:
            raise AgentProviderFailure(
                code="artifact_resolution_failed",
                message="Agent artifact resolver is not configured.",
                retriable=False,
            )
        return [
            await asyncio.to_thread(self._artifact_resolver.resolve, reference)
            for reference in request.artifact_references
        ]

    @staticmethod
    def _cost_metadata(usage: Usage | None) -> dict[str, object]:
        """Map optional provider usage into safe audit cost metadata."""

        if usage is None:
            return {}
        return {
            key: value
            for key, value in {
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            }.items()
            if value is not None
        }
