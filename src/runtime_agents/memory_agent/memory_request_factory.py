from __future__ import annotations

import json
from typing import Any

from ...llm.contract_kinds import MEMORY_DAILY_OUTPUT_KIND, MEMORY_ROLLING_OUTPUT_KIND
from ...llm.tasks.helpers.task_request_builder import ProviderRequestParts
from .contracts.daily import DailyMemoryContract, DailyMemoryInputContract
from .contracts.rolling import RollingMemoryContract, RollingMemoryInputContract
from .payload_normalizer import normalize_memory_payload_for_json

DAILY_MEMORY_RUNTIME_INSTRUCTIONS = (
    "Return only a JSON object in the daily memory contract format.\n"
    "Allowed top-level keys: daily_summary, conversation_state_update, active_window_update.\n"
    "Required: daily_summary.\n"
    "Required fields: daily_summary.summary_text.\n"
    "Forbidden: rolling_update, reply_text, system_payload, user-facing text, any envelope/wrapper, any top-level keys outside the daily memory contract.\n"
    "Optional blocks may be omitted when unnecessary.\n"
    "Do not return null for required blocks.\n"
    "Do not add empty artificial wrappers."
)

ROLLING_MEMORY_RUNTIME_INSTRUCTIONS = (
    "Return only a JSON object in the rolling memory contract format.\n"
    "Allowed top-level key: rolling_update.\n"
    "Required: rolling_update.\n"
    "Required fields: rolling_update.rolling_summary_text, rolling_update.days_count, rolling_update.last_daily_summary_date, rolling_update.version.\n"
    "Forbidden: daily_summary, active_window_update, conversation_state_update, reply_text, system_payload, user-facing text, any envelope/wrapper.\n"
    "Do not return null for required blocks."
)

_DAILY_INPUT_KEYS: tuple[str, ...] = (
    "lead_snapshot",
    "closed_active_window",
    "conversation_state",
    "timezone",
)

_ROLLING_INPUT_KEYS: tuple[str, ...] = (
    "prior_rolling_memory",
    "new_daily_summary",
)


def _build_daily_memory_input(payload: dict[str, Any]) -> str:
    normalized = normalize_memory_payload_for_json({key: payload.get(key) for key in _DAILY_INPUT_KEYS})
    typed = DailyMemoryInputContract.model_validate(normalized)
    return json.dumps(typed.model_dump(mode="python"), ensure_ascii=False)


def _build_rolling_memory_input(payload: dict[str, Any]) -> str:
    normalized = normalize_memory_payload_for_json({key: payload.get(key) for key in _ROLLING_INPUT_KEYS})
    typed = RollingMemoryInputContract.model_validate(normalized)
    return json.dumps(typed.model_dump(mode="python"), ensure_ascii=False)


def build_memory_daily_provider_request(payload: dict[str, Any]) -> ProviderRequestParts:
    return ProviderRequestParts(
        model=payload["model"],
        instructions=DAILY_MEMORY_RUNTIME_INSTRUCTIONS,
        input=_build_daily_memory_input(payload),
        structured_output={
            "kind": MEMORY_DAILY_OUTPUT_KIND,
            "strict": True,
            "schema": DailyMemoryContract.model_json_schema(),
        },
    )


def build_memory_rolling_provider_request(payload: dict[str, Any]) -> ProviderRequestParts:
    return ProviderRequestParts(
        model=payload["model"],
        instructions=ROLLING_MEMORY_RUNTIME_INSTRUCTIONS,
        input=_build_rolling_memory_input(payload),
        structured_output={
            "kind": MEMORY_ROLLING_OUTPUT_KIND,
            "strict": True,
            "schema": RollingMemoryContract.model_json_schema(),
        },
    )


def build_provider_request(payload: dict[str, Any]) -> ProviderRequestParts:
    return build_memory_daily_provider_request(payload)
