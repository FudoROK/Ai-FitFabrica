from __future__ import annotations

import logging
import time
from typing import Any, Optional

from src.llm.reply_task_contract import REPLY_RUNTIME_TASKS
from src.llm.vertex.vertex_schema_builder import build_vertex_response_schema

from ...settings import load_settings
from ..core.request import LLMRequest
from ..core.result import LLMResult
from ..vertex.vertex_errors import build_error_result, classify_provider_exception
from .gemini_structured_client import (
    genai,
    get_client,
    invoke_model,
    types,
)
from .gemini_structured_models import StructuredReasoningResult
from .gemini_structured_payloads import extract_payload, validate_payload_for_task
from .gemini_structured_schema import resolve_contract_kind, resolve_response_schema

logger = logging.getLogger(__name__)
_REPLY_RUNTIME_TASKS = REPLY_RUNTIME_TASKS


class GeminiStructuredProvider:
    provider_name = "gemini_structured"
    supports_artifacts = True

    def __init__(self, *, settings=None, timeout_s: float = 120.0) -> None:
        runtime_settings = settings or load_settings()
        self.project = runtime_settings.llm.vertex_project
        self.location = runtime_settings.llm.vertex_location or "us-central1"
        self.model = runtime_settings.llm.model or "gemini-2.0-flash"
        self.timeout_s = timeout_s
        self._model_clients: dict[str, Any] = {}

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
            model=self.model,
            error_type="unknown",
            message="Unknown Gemini structured generation failure",
            retriable=False,
        )

    def generate_structured(self, request: Any) -> StructuredReasoningResult:
        llm_result = self.generate(
            LLMRequest(
                task=request.task,
                input=request.prompt,
                structured_output={"name": request.task, "schema": request.response_schema},
            )
        )
        if llm_result.status != "ok" or not isinstance(llm_result.structured_data, dict):
            message = llm_result.error.message_redacted if llm_result.error is not None else "structured reasoning failed"
            raise RuntimeError(message)
        return StructuredReasoningResult(
            task=request.task,
            payload=llm_result.structured_data,
            provider=llm_result.provider or self.provider_name,
            model=llm_result.model or self.model,
        )

    def _generate_once(self, *, request: LLMRequest, started: float, retry_count: int) -> LLMResult:
        selected_model = request.model or self.model
        try:
            timeout_s = float(request.timeout_s or self.timeout_s)
            schema_resolution = self._resolve_response_schema(request=request, started=started, retry_count=retry_count)
            if schema_resolution["error_result"] is not None:
                return schema_resolution["error_result"]
            schema = schema_resolution["response_schema"]
            contract_kind = schema_resolution["contract_kind"]
            response_mime_type = "application/json"
            logger.info(
                "GEMINI_STRUCTURED_PROVIDER_INVOKED",
                extra={
                    "provider": self.provider_name,
                    "model": selected_model,
                    "response_schema_attached": True,
                    "response_mime_type": response_mime_type,
                    "timeout_s": timeout_s,
                    "contract_kind": contract_kind,
                },
            )
            response = self._invoke_model(
                request=request,
                model=selected_model,
                response_schema=schema,
                response_mime_type=response_mime_type,
                timeout_s=timeout_s,
            )
            payload = self._extract_payload(response, contract_kind=contract_kind)
            output = self._validate_payload_for_task(request=request, payload=payload)
            logger.info(
                "GEMINI_STRUCTURED_VALIDATION_SUCCESS",
                extra={"provider": self.provider_name, "model": selected_model},
            )
            return LLMResult(
                status="ok",
                text=__import__("json").dumps(output, ensure_ascii=False),
                structured_data=output,
                provider=self.provider_name,
                model=selected_model,
                latency_ms=int((time.perf_counter() - started) * 1000),
                retry_count=retry_count,
                usage=None,
                provider_metadata={
                    "execution_path": "gemini_direct_structured_generate_content",
                    "response_schema_attached": True,
                    "response_mime_type": response_mime_type,
                    "backend_validation": "json_object_only",
                    "runtime_contract_version": "google_genai_structured_contract_v1",
                    "contract_kind": contract_kind,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "GEMINI_STRUCTURED_PROVIDER_ERROR",
                extra={"provider": self.provider_name, "model": selected_model},
            )
            return self._classify_exception(exc=exc, started=started, retry_count=retry_count, model=selected_model)

    def _invoke_model(
        self,
        *,
        request: LLMRequest,
        model: str,
        response_schema: dict[str, Any],
        response_mime_type: str,
        timeout_s: float,
    ) -> Any:
        self._model_clients[model] = get_client(
            current_client=self._model_clients.get(model),
            project=self.project,
            location=self.location,
            genai_module=genai,
        )
        return invoke_model(
            client=self._model_clients[model],
            model=model,
            request=request,
            response_schema=response_schema,
            response_mime_type=response_mime_type,
            timeout_s=timeout_s,
            types_module=types,
        )

    def _get_model_client(self) -> Any:
        self._model_clients[self.model] = get_client(
            current_client=self._model_clients.get(self.model),
            project=self.project,
            location=self.location,
            genai_module=genai,
        )
        return self._model_clients[self.model]

    def _extract_payload(self, response: Any, *, contract_kind: str) -> dict[str, Any]:
        return extract_payload(response, contract_kind=contract_kind)

    def _validate_payload_for_task(self, *, request: LLMRequest, payload: dict[str, Any]) -> dict[str, Any]:
        return validate_payload_for_task(request=request, payload=payload)

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

    def _resolve_response_schema(self, *, request: LLMRequest, started: float, retry_count: int) -> dict[str, Any]:
        return resolve_response_schema(
            request=request,
            build_error_result=build_error_result,
            build_vertex_response_schema=build_vertex_response_schema,
            started=started,
            retry_count=retry_count,
            model=self.model,
            provider_name=self.provider_name,
        )

    @staticmethod
    def _resolve_contract_kind(request: LLMRequest, structured_output: dict[str, Any] | None) -> str:
        return resolve_contract_kind(request, structured_output)


__all__ = [
    "GeminiStructuredProvider",
    "StructuredReasoningResult",
    "genai",
    "types",
    "build_vertex_response_schema",
]
