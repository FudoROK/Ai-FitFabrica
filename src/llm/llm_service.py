from __future__ import annotations

import logging
import time
from typing import Any

from ..settings import load_settings
from .llm_base_contracts import LLMMeta, LLMResult, TaskName
from .core.result import LLMResult as CoreLLMResult
from .provider_runtime import ProviderRuntime, build_provider_runtime
from .provider_routing import ProviderRoutingDecision, select_provider_path
from .providers.base import LLMProvider
from .providers.registry import get_provider
from .reply_task_contract import REPLY_RUNTIME_TASKS
from .llm_task_registry import get_task_implementation, validate_task_registry
from .tasks.helpers.task_request_builder import ProviderRequestParts, provider_parts_to_core_request
from .tasks.profile_extract_task import register_profile_extract_schema

logger = logging.getLogger(__name__)
_REPLY_RUNTIME_TASKS = REPLY_RUNTIME_TASKS


class LLMService:
    def __init__(
        self,
        provider: LLMProvider | None = None,
        *,
        mode: str | None = None,
        model: str | None = None,
        settings=None,
        provider_runtime: ProviderRuntime | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.mode = (mode or self.settings.llm.mode or "stub").strip().lower()
        self.model = model or self.settings.llm.model
        self.provider = provider or get_provider(self.settings)
        self.provider_runtime = provider_runtime or build_provider_runtime(self.settings)
        self._structured_runtime_provider: LLMProvider | None = None
        register_profile_extract_schema()
        validate_task_registry()

    @property
    def _reply_structured_provider(self) -> LLMProvider | None:  # backward-compatible test seam
        return self._structured_runtime_provider

    @_reply_structured_provider.setter
    def _reply_structured_provider(self, value: LLMProvider | None) -> None:  # backward-compatible test seam
        self._structured_runtime_provider = value

    async def run(self, task: TaskName, payload: dict[str, Any], meta: LLMMeta | None = None) -> LLMResult:
        llm_meta = meta or LLMMeta()
        if self.mode != "live":
            return self._stub_result(task)

        started = time.perf_counter()
        task_module = get_task_implementation(task)
        prepared_payload = dict(payload)
        prepared_payload.setdefault("model", self.model)

        try:
            selected_provider, routing = self._select_provider_for_task(task)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "LLM_PROVIDER_SELECTION_FAILED",
                extra={
                    "task": task,
                    "trace_id": llm_meta.trace_id,
                    "execution_path": "provider_selection_failed",
                    "reply_path": "provider_selection_failed",
                    "structured_provider_used": True,
                },
            )
            return self._controlled_routing_error(task=task, reason=str(exc))

        provider_parts: ProviderRequestParts = task_module.build_provider_request(prepared_payload, llm_meta)
        provider_name = getattr(selected_provider, "provider_name", "unknown")
        logger.info(
            "LLM_PROMPT_ATTACHED",
            extra={
                "task": task,
                "provider": provider_name,
                "prompt_size": len(provider_parts.input or ""),
            },
        )
        logger.info(
            "LLM_REQUEST_STARTED",
            extra={
                "task": task,
                "provider": provider_name,
                "trace_id": llm_meta.trace_id,
                "lead_id": llm_meta.lead_id,
                "reply_path": routing.path_name,
                "execution_path": routing.path_name,
                "structured_provider_used": routing.structured_provider_used,
            },
        )

        core_request = provider_parts_to_core_request(provider_parts, task=task, meta=llm_meta, max_retries=1)
        provider_result: CoreLLMResult = selected_provider.generate(core_request)

        try:
            data = task_module.parse_provider_response(provider_result)
            latency_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "LLM_RESPONSE_RECEIVED",
                extra={
                    "task": task,
                    "provider": provider_name,
                    "provider_name": provider_name,
                    "model": provider_result.model,
                    "latency_ms": latency_ms,
                    "status": "ok",
                    "retry_count": provider_result.retry_count,
                    "trace_id": llm_meta.trace_id,
                    "reply_path": routing.path_name,
                    "execution_path": routing.path_name,
                    "backend_validation_ok": True,
                    "structured_provider_used": routing.structured_provider_used,
                },
            )
            return LLMResult(task=task, ok=True, data=data, provider_metadata=provider_result.provider_metadata or None)
        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.perf_counter() - started) * 1000)
            error_type = provider_result.error.type if provider_result.error else "invalid_output"
            logger.exception(
                "LLM_TASK_FAILED",
                extra={
                    "task": task,
                    "provider": provider_name,
                    "provider_name": provider_name,
                    "model": provider_result.model,
                    "latency_ms": latency_ms,
                    "status": "failed",
                    "retry_count": provider_result.retry_count,
                    "error_type": error_type,
                    "trace_id": llm_meta.trace_id,
                    "reply_path": routing.path_name,
                    "execution_path": routing.path_name,
                    "backend_validation_ok": False,
                    "structured_provider_used": routing.structured_provider_used,
                },
            )
            return self._error_result(task, provider_result, str(exc))

    def _stub_result(self, task: TaskName) -> LLMResult:
        if task in _REPLY_RUNTIME_TASKS:
            return LLMResult(task=task, ok=False, data={"reply_text": "", "system_payload": None}, error={"kind": "NON_LIVE", "message": "reply_unavailable"})
        return LLMResult(task=task, ok=False, error={"kind": "NON_LIVE", "message": "non_live_mode"})

    def _controlled_routing_error(self, *, task: TaskName, reason: str) -> LLMResult:
        message = f"structured_provider_unavailable: {reason}"
        if task in _REPLY_RUNTIME_TASKS:
            return LLMResult(
                task=task,
                ok=False,
                data={"reply_text": "", "system_payload": None},
                error={"kind": "ROUTING_ERROR", "message": message},
            )
        return LLMResult(task=task, ok=False, error={"kind": "ROUTING_ERROR", "message": message})

    def _error_result(self, task: TaskName, provider_result: CoreLLMResult, fallback_message: str) -> LLMResult:
        kind = provider_result.error.type if provider_result.error else "UNKNOWN"
        if isinstance(kind, str) and kind.lower() == "unknown":
            kind = "UNKNOWN"
        message = provider_result.error.message_redacted if provider_result.error else fallback_message
        if task in _REPLY_RUNTIME_TASKS:
            return LLMResult(
                task=task,
                ok=False,
                data={"reply_text": "", "system_payload": None},
                error={"kind": kind, "message": message},
            )
        return LLMResult(task=task, ok=False, error={"kind": kind, "message": message})

    def _select_provider_for_task(self, task: TaskName) -> tuple[LLMProvider, ProviderRoutingDecision]:
        routing = select_provider_path(task)
        if task in _REPLY_RUNTIME_TASKS:
            structured_provider = self._structured_runtime_provider or self.provider_runtime.structured_reasoning
            if structured_provider is None:
                raise RuntimeError("structured_provider_unavailable: configure provider_runtime.structured_reasoning")
            return structured_provider, ProviderRoutingDecision(path_name="structured_reasoning", structured_provider_used=True)
        if routing.path_name == "agent_runtime" and self._structured_runtime_provider is not None:
            return self._structured_runtime_provider, routing
        if not routing.structured_provider_used:
            return self.provider, routing

        structured_provider = self._structured_runtime_provider or self.provider_runtime.structured_reasoning
        if structured_provider is None:
            raise RuntimeError("structured_provider_unavailable: configure provider_runtime.structured_reasoning")
        return structured_provider, routing
