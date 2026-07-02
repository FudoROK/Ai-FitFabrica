from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import time
from typing import Any, Optional

from ..vertex.vertex_errors import build_error_result, classify_provider_exception
from ..vertex.vertex_identity import build_vertex_identity_payload
from ..vertex.vertex_invocation import invoke_session_flow
from ..vertex.vertex_schema_builder import build_vertex_structured_contract
from ..vertex.vertex_session import get_client

from ...settings import load_settings
from ..core.request import LLMRequest
from ..core.result import LLMResult

_VERTEXAI_SPEC = importlib.util.find_spec("vertexai")
agent_engines = importlib.import_module("vertexai.agent_engines") if _VERTEXAI_SPEC is not None else None
# Backward-compatible module alias used by tests/monkeypatch hooks.
reasoning_engines = agent_engines
logger = logging.getLogger(__name__)


class VertexProvider:
    provider_name = "vertex"
    supports_artifacts = False

    def __init__(
        self,
        *,
        settings=None,
        timeout_s: float = 120.0,
        agent_resource_override: str | None = None,
    ) -> None:
        runtime_settings = settings or load_settings()
        self.project = runtime_settings.llm.vertex_project
        self.location = runtime_settings.llm.vertex_location or "us-central1"
        self.model = runtime_settings.llm.model or "gemini-2.0-flash"
        self.agent_resource = agent_resource_override or runtime_settings.llm.vertex_agent_resource
        self.timeout_s = timeout_s
        self.client = None

    def generate(self, request: LLMRequest) -> LLMResult:
        started = time.perf_counter()
        retries = max(0, request.max_retries)
        last_result: Optional[LLMResult] = None

        for attempt in range(retries + 1):
            result = self._generate_once(request=request, started=started, retry_count=attempt)
            if result.status == "ok":
                return result
            last_result = result
            if not result.error or not result.error.retriable:
                break

        return last_result or self._error_result(
            started=started,
            retry_count=retries,
            model=self.agent_resource or self.model,
            error_type="unknown",
            message="Unknown Vertex generation failure",
            retriable=False,
        )

    def _generate_once(self, *, request: LLMRequest, started: float, retry_count: int) -> LLMResult:
        timeout_s = float(request.timeout_s or self.timeout_s)
        agent_resource = self.agent_resource

        try:
            if not agent_resource:
                raise ValueError("VERTEX_AGENT_RESOURCE is not configured")

            payload = self._build_agent_payload(request)
            logger.info(
                "VERTEX_AGENT_INVOCATION_START",
                extra={
                    "vertex_agent_resource": agent_resource,
                    "user_id": payload["user_id"],
                    "session_id": payload.get("session_id"),
                    "has_context": bool(payload.get("context")),
                    "message_len": len(payload["message"]),
                },
            )

            response = invoke_session_flow(
                client=self._get_client(),
                agent_resource=agent_resource,
                user_id=payload["user_id"],
                incoming_session_id=payload.get("session_id"),
                message=payload["message"],
                context=payload.get("context") or {},
                structured_contract=self._build_structured_contract(request),
                correlation_id=str(request.metadata.get("correlation_id") or "") or None,
                timeout_s=timeout_s,
                logger=logger,
            )

            text = json.dumps(response["output"], ensure_ascii=False)
            return LLMResult(
                status="ok",
                text=text,
                structured_data=response["output"],
                provider=self.provider_name,
                model=agent_resource,
                latency_ms=int((time.perf_counter() - started) * 1000),
                retry_count=retry_count,
                usage=None,
                provider_metadata={
                    "vertex_location": self.location,
                    "vertex_agent_resource": agent_resource,
                    "execution_path": "reasoning_engine_session_stream",
                    "response_mime_type": "application/json",
                    "vertex_user_id": payload["user_id"],
                    "vertex_session_id": response["session_id"],
                    "vertex_session_created": response["session_created"],
                    "vertex_event_count": response["event_count"],
                    "vertex_structured_requested": response.get("structured_requested"),
                    "vertex_structured_enforced": response.get("structured_enforced"),
                    "vertex_structured_mode": response.get("structured_mode"),
                    "contract_kind": response.get("structured_contract_kind"),
                    "contract_required": response.get("structured_contract_required"),
                    "contract_enforced": response.get("structured_enforced"),
                    "runtime_contract_version": "vertex_transport_blackbox_v1",
                },
            )

        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "VERTEX_AGENT_INVOCATION_ERROR",
                extra={
                    "vertex_agent_resource": agent_resource,
                    "provider": self.provider_name,
                },
            )
            return self._classify_exception(
                exc=exc,
                started=started,
                retry_count=retry_count,
                model=agent_resource or self.model,
            )

    def _build_agent_payload(self, request: LLMRequest) -> dict[str, Any]:
        return build_vertex_identity_payload(
            raw_input=request.input,
            request_context=request.context,
            request_metadata=request.metadata,
        )

    @staticmethod
    def _build_structured_contract(request: LLMRequest) -> dict[str, Any] | None:
        structured = request.structured_output if isinstance(request.structured_output, dict) else None
        return build_vertex_structured_contract(
            task=request.task,
            structured_output=structured,
        )

    def _get_client(self) -> Any:
        self.client = get_client(
            cached_client=self.client,
            reasoning_engines=reasoning_engines,
            agent_resource=self.agent_resource,
        )
        return self.client

    def _classify_exception(self, *, exc: Exception, started: float, retry_count: int, model: str) -> LLMResult:
        return classify_provider_exception(
            exc=exc,
            started=started,
            retry_count=retry_count,
            model=model,
            provider_name=self.provider_name,
        )

    def _error_result(
        self,
        *,
        started: float,
        retry_count: int,
        model: str,
        error_type: str,
        message: str,
        retriable: bool,
        http_status: int | None = None,
    ) -> LLMResult:
        return build_error_result(
            started=started,
            retry_count=retry_count,
            model=model,
            provider_name=self.provider_name,
            error_type=error_type,
            message=message,
            retriable=retriable,
            http_status=http_status,
        )
