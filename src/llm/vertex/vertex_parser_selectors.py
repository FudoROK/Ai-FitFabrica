"""Contract-aware selector functions for Vertex structured payload parsing."""
from __future__ import annotations

from typing import Any

from ..contract_kinds import (
    REPLY_AGENT_OUTPUT_KIND,
    canonicalize_contract_kind,
)

SERVICE_ONLY_KEYS = {"thought_signature", "text", "agent_name"}
CANONICAL_REPLY_KEYS = {"reply_text", "system_payload"}


def resolve_contract_selector(*, contract_kind: str | None) -> Any:
    normalized = canonicalize_contract_kind(contract_kind)
    if normalized == REPLY_AGENT_OUTPUT_KIND:
        return select_canonical_reply_envelope_candidate
    raise ValueError(f"contract routing violation: unknown contract_kind '{contract_kind}'")


def selector_mode_name(*, contract_kind: str | None) -> str:
    normalized = canonicalize_contract_kind(contract_kind)
    if normalized == REPLY_AGENT_OUTPUT_KIND:
        return "reply_envelope_contract"
    raise ValueError(f"contract routing violation: unknown contract_kind '{contract_kind}'")


def is_memory_contract_kind(contract_kind: str | None) -> bool:
    _ = contract_kind
    return False


def select_canonical_reply_envelope_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload")
    path = str(candidate.get("path") or "")
    depth = int(candidate.get("depth") or 0)
    if not isinstance(payload, dict):
        return {"is_valid": False, "reason": "payload_is_not_dict", "score": -1, "selector_rule": "payload_is_not_dict"}
    keys = set(payload.keys())
    if SERVICE_ONLY_KEYS.intersection(keys) and keys != CANONICAL_REPLY_KEYS:
        return {
            "is_valid": False,
            "reason": "service_keys_without_reply_contract",
            "score": 0,
            "selector_rule": "service_keys_without_reply_contract",
        }
    if keys != CANONICAL_REPLY_KEYS:
        return {
            "is_valid": False,
            "reason": "shape_not_canonical_reply_envelope",
            "score": 0,
            "selector_rule": "shape_not_canonical_reply_envelope",
        }
    if not isinstance(payload.get("reply_text"), str) or not isinstance(payload.get("system_payload"), dict):
        return {
            "is_valid": False,
            "reason": "invalid_reply_envelope_types",
            "score": 0,
            "selector_rule": "invalid_reply_envelope_types",
        }
    score = location_score(path) - depth
    return {
        "is_valid": True,
        "reason": f"canonical_reply_envelope@{location_label(path)}",
        "score": score,
        "selector_rule": "canonical_reply_envelope",
    }


def location_score(path: str) -> int:
    if ".output" in path:
        return 300
    if ".function_call.arguments" in path or ".function_call.args" in path:
        return 200
    if ".functionCall.arguments" in path or ".functionCall.args" in path:
        return 200
    return 100


def location_label(path: str) -> str:
    if ".output" in path:
        return "top_level_output"
    if ".function_call.arguments" in path or ".function_call.args" in path:
        return "function_call_arguments"
    if ".functionCall.arguments" in path or ".functionCall.args" in path:
        return "functionCall_arguments"
    return "nested_misc_dict"
