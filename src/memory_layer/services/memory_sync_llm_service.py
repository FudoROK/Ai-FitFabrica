"""LLM generation logic for lead memory summaries."""
from __future__ import annotations

import logging
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any, Optional

from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract
from src.runtime_agents.memory_agent.contracts.rolling import RollingMemoryContract
from src.runtime_agents.memory_agent.payload_normalizer import normalize_memory_payload_for_json
from src.llm.tasks.helpers.memory_output_parser import parse_memory_output_payload, parse_rolling_output_payload
from src.llm import LLMMeta, LLMService
from src.settings import load_settings
from src.utils.log_redaction import redact

logger = logging.getLogger(__name__)

_MEMORY_SHAPE_BLOCKS = (
    "daily_summary",
    "conversation_state_update",
    "active_window_update",
)
_MAX_KEY_PREVIEW = 20


def _preview_keys(value: dict[str, Any]) -> list[str]:
    return [str(key) for key in value.keys()][:_MAX_KEY_PREVIEW]


def _shape_type_name(value: Any) -> str:
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    if isinstance(value, str):
        return "str"
    if value is None:
        return "none"
    return type(value).__name__


def _normalized_shape_signature(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalized_shape_signature(value[key])
            for key in sorted(value.keys(), key=lambda key: str(key))
        }
    if isinstance(value, list):
        item_types = sorted({_shape_type_name(item) for item in value})
        return {"type": "list", "len": len(value), "item_types": item_types}
    return _shape_type_name(value)


def _memory_parser_input_shape(payload: dict[str, Any]) -> dict[str, Any]:
    top_level_keys = _preview_keys(payload)
    nested_blocks: dict[str, Any] = {}
    for block_name in _MEMORY_SHAPE_BLOCKS:
        block_value = payload.get(block_name)
        block_shape: dict[str, Any] = {
            "type": _shape_type_name(block_value),
        }
        if isinstance(block_value, dict):
            block_shape["keys"] = _preview_keys(block_value)
            block_shape["key_count"] = len(block_value)
        nested_blocks[block_name] = block_shape

    signature_payload = {
        "top_level_keys": sorted([str(key) for key in payload.keys()]),
        "top_level_key_count": len(payload),
        "nested_blocks": {
            name: _normalized_shape_signature(payload.get(name))
            for name in _MEMORY_SHAPE_BLOCKS
        },
    }
    signature_json = json.dumps(
        signature_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    shape_fingerprint = hashlib.sha256(signature_json.encode("utf-8")).hexdigest()[:16]

    return {
        "top_level_keys": top_level_keys,
        "top_level_key_count": len(payload),
        "nested_blocks": nested_blocks,
        "shape_fingerprint": shape_fingerprint,
    }


class MemorySummaryService:
    """Encapsulates LLM call for daily memory summary runtime output."""

    def __init__(self, *, llm_service: Optional[LLMService] = None, settings=None) -> None:
        if settings is not None:
            self.settings = settings
        elif llm_service is None:
            self.settings = load_settings()
        else:
            self.settings = None

        self.llm_service = llm_service or LLMService(settings=self.settings)


    async def _run_memory_daily_task(
        self,
        *,
        lead_id: str,
        correlation_id: str | None,
        lead_profile: dict[str, str],
        active_window: dict | None,
        conversation_state: dict | None,
        messages: list[dict],
    ) -> tuple[Any, bool, str | None]:
        """Run canonical memory sync task for daily memory output generation."""
        local_day_key = None
        if isinstance(active_window, dict):
            local_day_key = active_window.get("local_day_key")

        started = time.perf_counter()
        logger.info(
            "memory_daily_sync_started",
            extra={
                "lead_id": lead_id,
                "correlation_id": correlation_id,
                "local_day_key": local_day_key,
            },
        )
        llm_daily = await self.llm_service.run(
            task="memory_daily_sync_task",
            payload=self._build_memory_sync_payload(
                lead_profile=lead_profile,
                active_window=active_window,
                conversation_state=conversation_state,
                messages=messages,
            ),
            meta=LLMMeta(lead_id=lead_id),
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "memory_daily_sync_latency_ms",
            extra={
                "lead_id": lead_id,
                "correlation_id": correlation_id,
                "local_day_key": local_day_key,
                "latency_ms": latency_ms,
            },
        )
        if llm_daily.ok:
            logger.info(
                "memory_daily_sync_succeeded",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "local_day_key": local_day_key,
                    "latency_ms": latency_ms,
                },
            )
        else:
            logger.warning(
                "memory_daily_sync_failed",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "local_day_key": local_day_key,
                    "latency_ms": latency_ms,
                    "error": redact(llm_daily.error),
                },
            )

        return llm_daily, True, local_day_key

    async def generate_memory_output(
        self,
        *,
        lead_id: str,
        correlation_id: str | None = None,
        lead_profile: dict[str, str],
        active_window: dict | None,
        conversation_state: dict | None,
        messages: list[dict],
    ) -> "MemoryOutputExtractionResult":
        logger.info(
            "MEMORY_AGENT_RUNTIME_PATH_SELECTED",
            extra={"path": "llm_service_structured", "lead_id": lead_id, "correlation_id": correlation_id},
        )
        llm_daily, memory_sync_used, local_day_key = await self._run_memory_daily_task(
            lead_id=lead_id,
            correlation_id=correlation_id,
            lead_profile=lead_profile,
            active_window=active_window,
            conversation_state=conversation_state,
            messages=messages,
        )

        if not llm_daily.ok:
            if llm_daily.error:
                logger.exception("LLM daily summary failed for %s: %s", lead_id, redact(llm_daily.error))
            return MemoryOutputExtractionResult(
                output=None,
                error_code="extraction_not_found",
                error_message="memory_output_missing",
            )

        candidate_payload = llm_daily.data
        if not isinstance(candidate_payload, dict):
            logger.warning("memory_transport_contract_invalid", extra={"lead_id": lead_id})
            return MemoryOutputExtractionResult(
                output=None,
                error_code="transport_contract_invalid",
                error_message="memory_transport_payload_not_object",
            )

        parser_input_shape = _memory_parser_input_shape(candidate_payload)
        logger.info(
            "MEMORY_PARSER_INPUT_SHAPE",
            extra={"lead_id": lead_id, "correlation_id": correlation_id, **parser_input_shape},
        )

        try:
            typed_output = parse_memory_output_payload(candidate_payload)
        except ValueError as exc:
            if memory_sync_used:
                logger.warning(
                    "memory_daily_contract_valid",
                    extra={
                        "lead_id": lead_id,
                        "correlation_id": correlation_id,
                        "local_day_key": local_day_key,
                        "valid": False,
                    },
                )
                logger.warning(
                    "memory_daily_semantics_valid",
                    extra={
                        "lead_id": lead_id,
                        "correlation_id": correlation_id,
                        "local_day_key": local_day_key,
                        "valid": False,
                    },
                )
            logger.warning(
                "memory_parser_contract_invalid",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "error": redact(exc),
                    **parser_input_shape,
                },
            )
            return MemoryOutputExtractionResult(
                output=None,
                error_code="parser_contract_invalid",
                error_message=str(exc),
            )

        if not typed_output.daily_summary.summary_text.strip():
            if memory_sync_used:
                logger.warning(
                    "memory_daily_contract_valid",
                    extra={
                        "lead_id": lead_id,
                        "correlation_id": correlation_id,
                        "local_day_key": local_day_key,
                        "valid": True,
                    },
                )
                logger.warning(
                    "memory_daily_semantics_valid",
                    extra={
                        "lead_id": lead_id,
                        "correlation_id": correlation_id,
                        "local_day_key": local_day_key,
                        "valid": False,
                    },
                )
            logger.warning("Empty daily summary for %s", lead_id)
        elif memory_sync_used:
            logger.info(
                "memory_daily_contract_valid",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "local_day_key": local_day_key,
                    "valid": True,
                },
            )
            logger.info(
                "memory_daily_semantics_valid",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "local_day_key": local_day_key,
                    "valid": True,
                },
            )

        return MemoryOutputExtractionResult(output=typed_output, error_code=None, error_message=None)

    async def generate_rolling_update(
        self,
        *,
        lead_id: str,
        correlation_id: str | None = None,
        prior_rolling_memory: dict | None,
        new_daily_summary: dict,
    ) -> "MemoryRollingOutputExtractionResult":
        llm_rolling, local_day_key = await self._run_memory_rolling_task(
            lead_id=lead_id,
            correlation_id=correlation_id,
            prior_rolling_memory=prior_rolling_memory,
            new_daily_summary=new_daily_summary,
        )

        if not llm_rolling.ok:
            if llm_rolling.error:
                logger.exception("LLM rolling summary failed for %s: %s", lead_id, redact(llm_rolling.error))
            return MemoryRollingOutputExtractionResult(
                output=None,
                error_code="extraction_not_found",
                error_message="rolling_output_missing",
            )

        candidate_payload = llm_rolling.data
        if not isinstance(candidate_payload, dict):
            logger.warning("memory_rolling_transport_contract_invalid", extra={"lead_id": lead_id})
            return MemoryRollingOutputExtractionResult(
                output=None,
                error_code="transport_contract_invalid",
                error_message="memory_rolling_payload_not_object",
            )

        try:
            typed_output = parse_rolling_output_payload(candidate_payload)
        except ValueError as exc:
            logger.warning(
                "memory_rolling_parser_contract_invalid",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "error": redact(exc),
                },
            )
            return MemoryRollingOutputExtractionResult(
                output=None,
                error_code="parser_contract_invalid",
                error_message=str(exc),
            )
        return MemoryRollingOutputExtractionResult(output=typed_output, error_code=None, error_message=None)

    async def _run_memory_rolling_task(
        self,
        *,
        lead_id: str,
        correlation_id: str | None,
        prior_rolling_memory: dict | None,
        new_daily_summary: dict,
    ) -> tuple[Any, str | None]:
        local_day_key = new_daily_summary.get("memory_day_key")
        started = time.perf_counter()
        logger.info(
            "memory_rolling_sync_started",
            extra={
                "lead_id": lead_id,
                "correlation_id": correlation_id,
                "local_day_key": local_day_key,
            },
        )
        llm_rolling = await self.llm_service.run(
            task="memory_rolling_sync_task",
            payload=self._build_rolling_sync_payload(
                prior_rolling_memory=prior_rolling_memory,
                new_daily_summary=new_daily_summary,
            ),
            meta=LLMMeta(lead_id=lead_id),
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "memory_rolling_sync_latency_ms",
            extra={
                "lead_id": lead_id,
                "correlation_id": correlation_id,
                "local_day_key": local_day_key,
                "latency_ms": latency_ms,
            },
        )
        if llm_rolling.ok:
            logger.info(
                "memory_rolling_sync_succeeded",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "local_day_key": local_day_key,
                    "latency_ms": latency_ms,
                },
            )
        else:
            logger.warning(
                "memory_rolling_sync_failed",
                extra={
                    "lead_id": lead_id,
                    "correlation_id": correlation_id,
                    "local_day_key": local_day_key,
                    "latency_ms": latency_ms,
                    "error": redact(llm_rolling.error),
                },
            )
        return llm_rolling, local_day_key

    @staticmethod
    def _build_memory_sync_payload(
        *,
        lead_profile: dict[str, str],
        active_window: dict | None,
        conversation_state: dict | None,
        messages: list[dict],
    ) -> dict[str, Any]:
        return normalize_memory_payload_for_json(
            {
                "lead_snapshot": lead_profile,
                "closed_active_window": {
                    **(active_window or {}),
                    "messages": messages,
                },
                "conversation_state": conversation_state or {},
                "timezone": (active_window or {}).get("timezone"),
            }
        )

    @staticmethod
    def _build_rolling_sync_payload(
        *,
        prior_rolling_memory: dict | None,
        new_daily_summary: dict,
    ) -> dict[str, Any]:
        return normalize_memory_payload_for_json(
            {
                "prior_rolling_memory": prior_rolling_memory or {},
                "new_daily_summary": new_daily_summary,
            }
        )


@dataclass(frozen=True)
class MemoryOutputExtractionResult:
    output: DailyMemoryContract | None
    error_code: str | None
    error_message: str | None

@dataclass(frozen=True)
class MemoryRollingOutputExtractionResult:
    output: RollingMemoryContract | None
    error_code: str | None
    error_message: str | None
