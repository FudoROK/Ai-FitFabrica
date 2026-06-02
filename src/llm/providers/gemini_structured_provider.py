from __future__ import annotations

from dataclasses import dataclass
import importlib
import importlib.util
import json
import logging
import time
from typing import Any, Optional

from src.llm.vertex.vertex_schema_builder import build_vertex_response_schema
from src.llm.vertex.vertex_schema_validator import validate_agent_output
from src.llm.reply_task_contract import REPLY_RUNTIME_TASKS

from ...settings import load_settings
from ..vertex.vertex_errors import build_error_result, classify_provider_exception
from ..core.request import LLMRequest
from ..core.result import LLMResult

logger = logging.getLogger(__name__)
_REPLY_RUNTIME_TASKS = REPLY_RUNTIME_TASKS

_VERTEXAI_SPEC = importlib.util.find_spec("vertexai")
vertexai = importlib.import_module("vertexai") if _VERTEXAI_SPEC is not None else None
generative_models = importlib.import_module("vertexai.generative_models") if _VERTEXAI_SPEC is not None else None


@dataclass(frozen=True)
class _StructuredReasoningResult:
    """Lightweight structured reasoning result returned by the Gemini provider."""

    task: str
    payload: dict[str, Any]
    provider: str
    model: str


class GeminiStructuredProvider:
    provider_name = "gemini_structured"

    def __init__(self, *, settings=None, timeout_s: float = 120.0) -> None:
        runtime_settings = settings or load_settings()
        self.project = runtime_settings.llm.vertex_project
        self.location = runtime_settings.llm.vertex_location or "us-central1"
        self.model = runtime_settings.llm.model or "gemini-2.0-flash"
        self.timeout_s = timeout_s
        self._model_client: Any = None

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

    def generate_structured(self, request: Any) -> _StructuredReasoningResult:
        """Run a backend-owned structured reasoning request through the Gemini JSON path."""
        llm_result = self.generate(
            LLMRequest(
                task=request.task,
                input=request.prompt,
                structured_output={
                    "name": request.task,
                    "schema": request.response_schema,
                },
            )
        )
        if llm_result.status != "ok" or not isinstance(llm_result.structured_data, dict):
            message = llm_result.error.message_redacted if llm_result.error is not None else "structured reasoning failed"
            raise RuntimeError(message)
        return _StructuredReasoningResult(
            task=request.task,
            payload=llm_result.structured_data,
            provider=llm_result.provider or self.provider_name,
            model=llm_result.model or self.model,
        )

    def _generate_once(self, *, request: LLMRequest, started: float, retry_count: int) -> LLMResult:
        try:
            timeout_s = float(request.timeout_s or self.timeout_s)
            schema_resolution = self._resolve_response_schema(
                request=request,
                started=started,
                retry_count=retry_count,
            )
            if schema_resolution["error_result"] is not None:
                return schema_resolution["error_result"]

            schema = schema_resolution["response_schema"]
            contract_kind = schema_resolution["contract_kind"]
            response_mime_type = "application/json"

            logger.info(
                "GEMINI_STRUCTURED_PROVIDER_INVOKED",
                extra={
                    "provider": self.provider_name,
                    "model": self.model,
                    "response_schema_attached": True,
                    "response_mime_type": response_mime_type,
                    "timeout_s": timeout_s,
                    "contract_kind": contract_kind,
                },
            )

            response = self._invoke_model(
                request=request,
                response_schema=schema,
                response_mime_type=response_mime_type,
                timeout_s=timeout_s,
            )

            payload = self._extract_payload(response, contract_kind=contract_kind)
            output = self._validate_payload_for_task(request=request, payload=payload)

            logger.info(
                "GEMINI_STRUCTURED_VALIDATION_SUCCESS",
                extra={
                    "provider": self.provider_name,
                    "model": self.model,
                },
            )

            return LLMResult(
                status="ok",
                text=json.dumps(output, ensure_ascii=False),
                structured_data=output,
                provider=self.provider_name,
                model=self.model,
                latency_ms=int((time.perf_counter() - started) * 1000),
                retry_count=retry_count,
                usage=None,
                provider_metadata={
                    "execution_path": "gemini_direct_structured_generate_content",
                    "response_schema_attached": True,
                    "response_mime_type": response_mime_type,
                    "backend_validation": "json_object_only",
                    "runtime_contract_version": "vertex_structured_contract_v2_direct",
                    "contract_kind": contract_kind,
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "GEMINI_STRUCTURED_PROVIDER_ERROR",
                extra={
                    "provider": self.provider_name,
                    "model": self.model,
                },
            )
            return self._classify_exception(exc=exc, started=started, retry_count=retry_count, model=self.model)

    def _invoke_model(
        self,
        *,
        request: LLMRequest,
        response_schema: dict[str, Any],
        response_mime_type: str,
        timeout_s: float,
    ) -> Any:
        model = self._get_model_client()
        generation_config = self._build_generation_config(
            response_schema=response_schema,
            response_mime_type=response_mime_type,
            temperature=request.temperature,
        )
        user_content = request.input

        try:
            return model.generate_content(
                user_content,
                generation_config=generation_config,
                stream=False,
                request_options={"timeout": timeout_s},
            )
        except TypeError:
            return model.generate_content(
                user_content,
                generation_config=generation_config,
                stream=False,
            )

    def _build_generation_config(
        self,
        *,
        response_schema: dict[str, Any],
        response_mime_type: str,
        temperature: float | None,
    ) -> Any:
        payload: dict[str, Any] = {
            "response_mime_type": response_mime_type,
            "response_schema": response_schema,
        }
        if temperature is not None:
            payload["temperature"] = temperature

        generation_config_cls = getattr(generative_models, "GenerationConfig", None) if generative_models else None
        if callable(generation_config_cls):
            return generation_config_cls(**payload)
        return payload

    def _get_model_client(self) -> Any:
        if self._model_client is not None:
            return self._model_client

        if vertexai is None or generative_models is None:
            raise RuntimeError("vertexai SDK with generative models is not installed")

        if not self.project:
            raise ValueError("VERTEX_PROJECT is not configured")

        init_fn = getattr(vertexai, "init", None)
        if callable(init_fn):
            init_fn(project=self.project, location=self.location)

        model_cls = getattr(generative_models, "GenerativeModel", None)
        if not callable(model_cls):
            raise RuntimeError("vertexai.generative_models.GenerativeModel is not available")

        self._model_client = model_cls(self.model)
        return self._model_client

    def _extract_payload(self, response: Any, *, contract_kind: str) -> dict[str, Any]:
        matcher = self._build_candidate_matcher(contract_kind)

        candidate = self._find_payload_candidate(response, matcher=matcher)
        if isinstance(candidate, dict):
            return candidate

        response_text = getattr(response, "text", None)
        if isinstance(response_text, str) and response_text.strip():
            parsed = json.loads(response_text)
            candidate = self._find_payload_candidate(parsed, matcher=matcher)
            if isinstance(candidate, dict):
                return candidate

        dumped = self._to_dict(response)
        candidate = self._find_payload_candidate(dumped, matcher=matcher)
        if isinstance(candidate, dict):
            return candidate

        raise ValueError(
            "invalid_output: Gemini structured provider response is missing JSON payload "
            f"matching contract '{contract_kind}'"
        )

    def _validate_payload_for_task(self, *, request: LLMRequest, payload: dict[str, Any]) -> dict[str, Any]:
        if request.task in _REPLY_RUNTIME_TASKS:
            ok, reason = validate_agent_output(payload)
            if not ok:
                raise ValueError(f"invalid_output: {reason}")
            return payload
        return payload

    def _find_payload_candidate(self, value: Any, *, matcher: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            if matcher(value):
                return value
            for child in value.values():
                nested = self._find_payload_candidate(child, matcher=matcher)
                if nested is not None:
                    return nested
            return None

        if isinstance(value, list):
            for item in value:
                nested = self._find_payload_candidate(item, matcher=matcher)
                if nested is not None:
                    return nested
            return None

        if hasattr(value, "to_dict"):
            dumped = value.to_dict()
            return self._find_payload_candidate(dumped, matcher=matcher)

        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            return self._find_payload_candidate(dumped, matcher=matcher)

        return None

    def _build_candidate_matcher(self, contract_kind: str):
        normalized = (contract_kind or "").strip()
        if normalized in _REPLY_RUNTIME_TASKS:
            return self._is_reply_payload
        if normalized == "memory_daily_output":
            return self._is_memory_payload
        if normalized == "memory_rolling_output":
            return self._is_memory_rolling_payload
        return lambda payload: isinstance(payload, dict)

    @staticmethod
    def _is_reply_payload(payload: dict[str, Any]) -> bool:
        return "reply_text" in payload and "system_payload" in payload

    @staticmethod
    def _is_memory_payload(payload: dict[str, Any]) -> bool:
        allowed_keys = {
            "daily_summary",
            "conversation_state_update",
            "active_window_update",
        }
        payload_keys = set(payload)
        if not payload_keys.issubset(allowed_keys):
            return False
        if "daily_summary" not in payload:
            return False
        return isinstance(payload.get("daily_summary"), dict)

    @staticmethod
    def _is_memory_rolling_payload(payload: dict[str, Any]) -> bool:
        if set(payload.keys()) != {"rolling_update"}:
            return False
        rolling_update = payload.get("rolling_update")
        if not isinstance(rolling_update, dict):
            return False
        required_keys = {
            "rolling_summary_text",
            "open_questions",
            "carry_forward_notes",
            "days_count",
            "last_daily_summary_date",
            "version",
        }
        return set(rolling_update.keys()) == required_keys

    def _to_dict(self, value: Any) -> dict[str, Any] | None:
        if isinstance(value, dict):
            return value
        if hasattr(value, "to_dict"):
            dumped = value.to_dict()
            if isinstance(dumped, dict):
                return dumped
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            if isinstance(dumped, dict):
                return dumped
        return None

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
        structured_output = request.structured_output if isinstance(request.structured_output, dict) else None
        schema = structured_output.get("schema") if structured_output else None

        if isinstance(schema, dict):
            return {
                "response_schema": schema,
                "contract_kind": self._resolve_contract_kind(request, structured_output),
                "error_result": None,
            }

        if request.task in _REPLY_RUNTIME_TASKS:
            return {
                "response_schema": build_vertex_response_schema(),
                "contract_kind": self._resolve_contract_kind(request, structured_output),
                "error_result": None,
            }

        return {
            "response_schema": {},
            "contract_kind": self._resolve_contract_kind(request, structured_output),
            "error_result": self._error_result(
                started=started,
                retry_count=retry_count,
                model=self.model,
                error_type="bad_request",
                message=(
                    "Structured output schema is required: request.structured_output must be a dict "
                    f"containing a dict schema for task '{request.task}'."
                ),
                retriable=False,
                http_status=400,
            ),
        }

    @staticmethod
    def _resolve_contract_kind(request: LLMRequest, structured_output: dict[str, Any] | None) -> str:
        name = structured_output.get("name") if isinstance(structured_output, dict) else None
        if isinstance(name, str) and name.strip():
            return name.strip()
        return request.task
