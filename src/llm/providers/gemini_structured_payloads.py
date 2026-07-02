from __future__ import annotations

import json
from typing import Any

from src.llm.reply_task_contract import REPLY_RUNTIME_TASKS
from src.llm.vertex.vertex_schema_validator import validate_agent_output


def find_payload_candidate(value: Any, *, matcher: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        if matcher(value):
            return value
        for child in value.values():
            nested = find_payload_candidate(child, matcher=matcher)
            if nested is not None:
                return nested
        return None
    if isinstance(value, list):
        for item in value:
            nested = find_payload_candidate(item, matcher=matcher)
            if nested is not None:
                return nested
        return None
    if hasattr(value, "to_dict"):
        return find_payload_candidate(value.to_dict(), matcher=matcher)
    if hasattr(value, "model_dump"):
        return find_payload_candidate(value.model_dump(), matcher=matcher)
    return None


def build_candidate_matcher(contract_kind: str):
    normalized = (contract_kind or "").strip()
    if normalized in REPLY_RUNTIME_TASKS:
        return is_reply_payload
    if normalized == "memory_daily_output":
        return is_memory_payload
    if normalized == "memory_rolling_output":
        return is_memory_rolling_payload
    return lambda payload: isinstance(payload, dict)


def is_reply_payload(payload: dict[str, Any]) -> bool:
    return "reply_text" in payload and "system_payload" in payload


def is_memory_payload(payload: dict[str, Any]) -> bool:
    allowed_keys = {"daily_summary", "conversation_state_update", "active_window_update"}
    payload_keys = set(payload)
    if not payload_keys.issubset(allowed_keys):
        return False
    return "daily_summary" in payload and isinstance(payload.get("daily_summary"), dict)


def is_memory_rolling_payload(payload: dict[str, Any]) -> bool:
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


def to_dict(value: Any) -> dict[str, Any] | None:
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


def extract_payload(response: Any, *, contract_kind: str) -> dict[str, Any]:
    matcher = build_candidate_matcher(contract_kind)
    response_text = getattr(response, "text", None)
    if isinstance(response_text, str) and response_text.strip():
        parsed = json.loads(response_text)
        candidate = find_payload_candidate(parsed, matcher=matcher)
        if isinstance(candidate, dict):
            return candidate
    candidate = find_payload_candidate(response, matcher=matcher)
    if isinstance(candidate, dict):
        return candidate
    dumped = to_dict(response)
    candidate = find_payload_candidate(dumped, matcher=matcher)
    if isinstance(candidate, dict):
        return candidate
    raise ValueError(
        "invalid_output: Gemini structured provider response is missing JSON payload "
        f"matching contract '{contract_kind}'"
    )


def validate_payload_for_task(*, request, payload: dict[str, Any]) -> dict[str, Any]:
    if request.task in REPLY_RUNTIME_TASKS:
        ok, reason = validate_agent_output(payload)
        if not ok:
            raise ValueError(f"invalid_output: {reason}")
    return payload
