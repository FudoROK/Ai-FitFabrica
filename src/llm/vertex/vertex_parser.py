from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from ...runtime_agents.memory_agent.contracts.daily import DailyMemoryContract
from ...runtime_agents.memory_agent.contracts.rolling import RollingMemoryContract
from ...runtime_agents.memory_agent.memory_response_mapper import map_runtime_payload
from ..contract_kinds import (
    MEMORY_DAILY_OUTPUT_KIND,
    MEMORY_ROLLING_OUTPUT_KIND,
    REPLY_AGENT_OUTPUT_KIND,
    canonicalize_contract_kind,
)
from ..transport.structured_extractor import collect_raw_structured_payload_candidates

logger = logging.getLogger(__name__)
_KEY_PREVIEW_LIMIT = 12
_NESTED_KEY_PREVIEW_LIMIT = 4
_SERVICE_ONLY_KEYS = {"thought_signature", "text", "agent_name"}
_CANONICAL_REPLY_KEYS = {"reply_text", "system_payload"}
_DAILY_CONTRACT_INVALID = "daily_contract_invalid"
_ROLLING_CONTRACT_INVALID = "rolling_contract_invalid"


def collect_output_from_events(
        events: list[Any],
        *,
        contract_selector: Any | None = None,
        contract_kind: str | None = None,
        correlation_id: str | None = None,
) -> dict[str, Any]:
    """Collect a structured payload from Vertex stream events using contract-aware selection."""
    selector = contract_selector or resolve_contract_selector(contract_kind=contract_kind)

    valid_candidates: list[dict[str, Any]] = []
    candidate_count = 0

    for event_index, event in enumerate(events):
        if is_memory_contract_kind(contract_kind):
            event_dict = event_to_dict(event)
            logger.info(
                "MEMORY_AGENT_EVENT_DIAGNOSTIC %s",
                {
                    "event_index": event_index,
                    "top_level_keys": list(event_dict.keys())[:_KEY_PREVIEW_LIMIT] if isinstance(event_dict,
                                                                                                 dict) else [],
                    "has_content_dict": isinstance(event_dict.get("content"), dict) if isinstance(event_dict,
                                                                                                  dict) else False,
                    "has_output": isinstance(event_dict.get("output"), dict) if isinstance(event_dict, dict) else False,
                    "has_function_call": (
                            isinstance(event_dict.get("function_call"), dict)
                            or isinstance(event_dict.get("functionCall"), dict)
                    ) if isinstance(event_dict, dict) else False,
                    "has_function_response": (
                            isinstance(event_dict.get("function_response"), dict)
                            or isinstance(event_dict.get("functionResponse"), dict)
                    ) if isinstance(event_dict, dict) else False,
                    "has_parts": isinstance(event_dict.get("parts"), list) if isinstance(event_dict, dict) else False,
                    "event_type": type(event).__name__,
                    "correlation_id": correlation_id,
                },
            )

        for candidate in collect_raw_structured_payload_candidates(event, event_index=event_index):
            candidate_count += 1
            selection = selector(candidate)

            if is_memory_contract_kind(contract_kind):
                payload = candidate.get("payload")
                preview = candidate_preview(payload) if isinstance(payload, dict) else {
                    "top_keys": [],
                    "top_key_count": 0,
                    "nested_shape": {},
                }
                logger.info(
                    "MEMORY_AGENT_CANDIDATE_DIAGNOSTIC %s",
                    {
                        "event_index": candidate.get("event_index"),
                        "path": candidate.get("path"),
                        "depth": candidate.get("depth"),
                        "top_keys": preview.get("top_keys", []),
                        "top_key_count": preview.get("top_key_count", 0),
                        "nested_shape": preview.get("nested_shape", {}),
                        "selector_rule": selection.get("selector_rule"),
                        "reason": selection.get("reason"),
                        "is_valid": bool(selection.get("is_valid")),
                        "correlation_id": correlation_id,
                    },
                )

            if not selection.get("is_valid"):
                logger.info(
                    "VERTEX_STRUCTURED_PAYLOAD_CANDIDATE_REJECTED %s",
                    {
                        "event_index": candidate.get("event_index"),
                        "path": candidate.get("path"),
                        "depth": candidate.get("depth"),
                        "candidate_preview": candidate_preview(candidate.get("payload") or {}),
                        "reason": selection.get("reason", "invalid_candidate"),
                        "selector_rule": selection.get("selector_rule"),
                        "correlation_id": correlation_id,
                    },
                )
                continue

            selected = {
                **candidate,
                "score": int(selection.get("score", 0)),
                "reason": str(selection.get("reason") or "valid_candidate"),
            }
            valid_candidates.append(selected)
            logger.info(
                "VERTEX_STRUCTURED_PAYLOAD_CANDIDATE_VALID %s",
                {
                    "event_index": selected["event_index"],
                    "path": selected["path"],
                    "depth": selected["depth"],
                    "score": selected["score"],
                    "reason": selected["reason"],
                    "selector_rule": selection.get("selector_rule"),
                    "candidate_preview": candidate_preview(selected.get("payload") or {}),
                    "correlation_id": correlation_id,
                },
            )

    if not valid_candidates:
        chunk_payload = _collect_json_payload_from_text_chunks(
            events=events,
            contract_kind=contract_kind,
            correlation_id=correlation_id,
        )
        if chunk_payload is not None:
            if is_memory_contract_kind(contract_kind):
                chunk_payload = map_runtime_payload(chunk_payload)
            return {
                "output": chunk_payload,
                "event_count": len(events),
            }

        if is_memory_contract_kind(contract_kind):
            logger.info(
                "MEMORY_AGENT_EXTRACTION_FAILURE_DIAGNOSTIC %s",
                {
                    "contract_kind": canonicalize_contract_kind(contract_kind),
                    "event_count": len(events),
                    "valid_structured_candidate_count": len(valid_candidates),
                    "used_text_fallback": True,
                    "correlation_id": correlation_id,
                },
            )

        if contract_kind == MEMORY_DAILY_OUTPUT_KIND:
            raise ValueError(f"{_DAILY_CONTRACT_INVALID}: no valid structured candidate")
        if contract_kind == MEMORY_ROLLING_OUTPUT_KIND:
            raise ValueError(f"{_ROLLING_CONTRACT_INVALID}: no valid structured candidate")
        raise ValueError("Vertex structured output extraction contract violation: no valid candidate")

    best = sorted(
        valid_candidates,
        key=lambda candidate: (
            -candidate["score"],
            -int(candidate["event_index"]),
            int(candidate["depth"]),
            str(candidate["path"]),
        ),
    )[0]
    payload = best.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Vertex structured output extraction contract violation: selected candidate is not a dict")
    if is_memory_contract_kind(contract_kind):
        payload = map_runtime_payload(payload)

    logger.info(
        "VERTEX_STRUCTURED_PAYLOAD_SELECTED %s",
        {
            "event_index": best["event_index"],
            "path": best["path"],
            "depth": best["depth"],
            "score": best["score"],
            "reason": best["reason"],
            "candidate_preview": candidate_preview(payload),
            "candidate_count": candidate_count,
            "valid_candidate_count": len(valid_candidates),
            "correlation_id": correlation_id,
        },
    )

    if is_memory_contract_kind(contract_kind):
        preview = candidate_preview(payload)
        logger.info(
            "MEMORY_AGENT_FINAL_PAYLOAD_DIAGNOSTIC %s",
            {
                "contract_kind": canonicalize_contract_kind(contract_kind),
                "source": "explicit_structured",
                "event_index": best["event_index"],
                "candidate_index": None,
                "payload_top_keys": preview.get("top_keys", []),
                "payload_top_key_count": preview.get("top_key_count", 0),
                "payload_nested_shape": preview.get("nested_shape", {}),
                "correlation_id": correlation_id,
            },
        )

    return {
        "output": payload,
        "event_count": len(events),
    }


def _collect_json_payload_from_text_chunks(
        *,
        events: list[Any],
        contract_kind: str | None,
        correlation_id: str | None,
) -> dict[str, Any] | None:
    chunks: list[str] = []
    for event in events:
        chunks.extend(_extract_event_text_chunks(event))
    if not chunks:
        return None

    raw_payload = "".join(chunks).strip()
    if not raw_payload:
        return None

    logger.info(
        "MEMORY_AGENT_RAW_TEXT_PAYLOAD %s",
        {
            "contract_kind": canonicalize_contract_kind(contract_kind),
            "event_count": len(events),
            "text_chunk_count": len(chunks),
            "raw_payload": raw_payload,
            "correlation_id": correlation_id,
        },
    )

    if is_memory_contract_kind(contract_kind):
        logger.info(
            "MEMORY_AGENT_TEXT_CHUNKS_DIAGNOSTIC %s",
            {
                "event_count": len(events),
                "text_chunk_count": len(chunks),
                "non_empty_chunks_count": sum(1 for chunk in chunks if chunk.strip()),
                "assembled_text_len": len(raw_payload),
                "correlation_id": correlation_id,
            },
        )

    normalized_payload = _normalize_streamed_text(raw_payload)
    json_candidates = _extract_json_object_candidates(normalized_payload)

    if is_memory_contract_kind(contract_kind):
        logger.info(
            "MEMORY_AGENT_JSON_CANDIDATES_DIAGNOSTIC %s",
            {
                "json_candidate_count": len(json_candidates),
                "correlation_id": correlation_id,
            },
        )

    parsed_candidates: list[dict[str, Any]] = []
    for candidate_index, candidate_text in enumerate(json_candidates):
        try:
            parsed_payload = json.loads(candidate_text)
        except json.JSONDecodeError:
            if is_memory_contract_kind(contract_kind):
                logger.info(
                    "MEMORY_AGENT_JSON_CANDIDATE_DIAGNOSTIC %s",
                    {
                        "candidate_index": candidate_index,
                        "candidate_len": len(candidate_text),
                        "json_parse_ok": False,
                        "correlation_id": correlation_id,
                    },
                )
            continue

        if is_memory_contract_kind(contract_kind):
            preview = candidate_preview(parsed_payload) if isinstance(parsed_payload, dict) else {
                "top_keys": [],
                "top_key_count": 0,
                "nested_shape": {},
            }
            logger.info(
                "MEMORY_AGENT_JSON_CANDIDATE_DIAGNOSTIC %s",
                {
                    "candidate_index": candidate_index,
                    "candidate_len": len(candidate_text),
                    "json_parse_ok": True,
                    "top_keys": preview.get("top_keys", []),
                    "top_key_count": preview.get("top_key_count", 0),
                    "nested_shape": preview.get("nested_shape", {}),
                    "correlation_id": correlation_id,
                },
            )

        if isinstance(parsed_payload, dict):
            logger.info(
                "MEMORY_AGENT_RAW_JSON_CANDIDATE %s",
                {
                    "candidate_index": candidate_index,
                    "contract_kind": canonicalize_contract_kind(contract_kind),
                    "parsed_payload": parsed_payload,
                    "correlation_id": correlation_id,
                },
            )
            parsed_candidates.append(parsed_payload)

    selector = resolve_contract_selector(contract_kind=contract_kind)
    for parsed_index, parsed_payload in enumerate(reversed(parsed_candidates)):
        candidate = {
            "payload": parsed_payload,
            "path": "event.content.parts.text_stream",
            "depth": 1,
            "event_index": max(0, len(events) - 1),
        }
        selection = selector(candidate)

        if is_memory_contract_kind(contract_kind):
            logger.info(
                "MEMORY_AGENT_JSON_CANDIDATE_VALIDATION_DIAGNOSTIC %s",
                {
                    "candidate_index": parsed_index,
                    "selector_rule": selection.get("selector_rule"),
                    "reason": selection.get("reason"),
                    "selector_is_valid": bool(selection.get("is_valid")),
                    "correlation_id": correlation_id,
                },
            )

        if not selection.get("is_valid"):
            continue

        if is_memory_contract_kind(contract_kind):
            preview = candidate_preview(parsed_payload)
            logger.info(
                "MEMORY_AGENT_FINAL_PAYLOAD_DIAGNOSTIC %s",
                {
                    "contract_kind": canonicalize_contract_kind(contract_kind),
                    "source": "stream_text_candidate",
                    "event_index": max(0, len(events) - 1),
                    "candidate_index": parsed_index,
                    "payload_top_keys": preview.get("top_keys", []),
                    "payload_top_key_count": preview.get("top_key_count", 0),
                    "payload_nested_shape": preview.get("nested_shape", {}),
                    "correlation_id": correlation_id,
                },
            )

        if not _validate_runtime_contract(contract_kind=contract_kind, payload=parsed_payload):
            if is_memory_contract_kind(contract_kind):
                logger.info(
                    "MEMORY_AGENT_JSON_CANDIDATE_VALIDATION_DIAGNOSTIC %s",
                    {
                        "candidate_index": parsed_index,
                        "selector_rule": selection.get("selector_rule"),
                        "reason": selection.get("reason"),
                        "runtime_validation_ok": False,
                        "correlation_id": correlation_id,
                    },
                )
            continue

        if is_memory_contract_kind(contract_kind):
            logger.info(
                "MEMORY_AGENT_JSON_CANDIDATE_VALIDATION_DIAGNOSTIC %s",
                {
                    "candidate_index": parsed_index,
                    "selector_rule": selection.get("selector_rule"),
                    "reason": selection.get("reason"),
                    "runtime_validation_ok": True,
                    "correlation_id": correlation_id,
                },
            )

        logger.info(
            "VERTEX_STREAM_TEXT_JSON_PAYLOAD_SELECTED %s",
            {
                "event_count": len(events),
                "chunk_count": len(chunks),
                "selector_rule": selection.get("selector_rule"),
                "reason": selection.get("reason"),
                "payload_preview": candidate_preview(parsed_payload),
                "candidate_count": len(json_candidates),
                "parsed_candidate_count": len(parsed_candidates),
                "correlation_id": correlation_id,
            },
        )
        if is_memory_contract_kind(contract_kind):
            return map_runtime_payload(parsed_payload)
        return parsed_payload

    if is_memory_contract_kind(contract_kind):
        logger.info(
            "MEMORY_AGENT_EXTRACTION_FAILURE_DIAGNOSTIC %s",
            {
                "contract_kind": canonicalize_contract_kind(contract_kind),
                "event_count": len(events),
                "text_chunk_count": len(chunks),
                "assembled_text_len": len(raw_payload),
                "json_candidate_count": len(json_candidates),
                "valid_structured_candidate_count": 0,
                "used_text_fallback": True,
                "correlation_id": correlation_id,
            },
        )

    raise ValueError(
        "Vertex structured output extraction contract violation: extraction/invalid_output in streamed text chunks"
    )


def _normalize_streamed_text(raw_payload: str) -> str:
    normalized = raw_payload.replace("```json", "").replace("```JSON", "").replace("```", "")
    return normalized.strip()


def _extract_json_object_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    start_index: int | None = None
    depth = 0
    in_string = False
    escaped = False

    for idx, char in enumerate(text):
        if start_index is None:
            if char == "{":
                start_index = idx
                depth = 1
                in_string = False
                escaped = False
            continue

        if in_string:
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            continue
        if char == "{":
            depth += 1
            continue
        if char == "}":
            depth -= 1
            if depth == 0:
                candidates.append(text[start_index: idx + 1])
                start_index = None
            continue
    return candidates


def _validate_runtime_contract(*, contract_kind: str | None, payload: dict[str, Any]) -> bool:
    normalized = canonicalize_contract_kind(contract_kind)
    try:
        if normalized == MEMORY_DAILY_OUTPUT_KIND:
            normalized_payload = map_runtime_payload(payload)
            logger.info(
                "MEMORY_AGENT_RUNTIME_VALIDATION_DIAGNOSTIC %s",
                {
                    "contract_kind": normalized,
                    "payload_top_keys": summarize_top_level_keys(normalized_payload),
                },
            )
            DailyMemoryContract.model_validate(normalized_payload)
        elif normalized == MEMORY_ROLLING_OUTPUT_KIND:
            normalized_payload = map_runtime_payload(payload)
            RollingMemoryContract.model_validate(normalized_payload)
        else:
            if not isinstance(payload.get("reply_text"), str):
                return False
            if not isinstance(payload.get("system_payload"), dict):
                return False
    except ValidationError as exc:
        if normalized == MEMORY_DAILY_OUTPUT_KIND:
            normalized_payload = map_runtime_payload(payload)
            logger.info(
                "MEMORY_AGENT_RUNTIME_VALIDATION_DIAGNOSTIC %s",
                {
                    "contract_kind": normalized,
                    "payload_top_keys": summarize_top_level_keys(normalized_payload),
                    "runtime_validation_ok": False,
                },
            )
            logger.error(
                "MEMORY_AGENT_RUNTIME_VALIDATION_ERROR %s",
                {
                    "contract_kind": normalized,
                    "payload": payload,
                    "normalized_payload": normalized_payload,
                    "validation_errors": exc.errors(include_url=False),
                },
            )
        return False

    if normalized in {MEMORY_DAILY_OUTPUT_KIND, MEMORY_ROLLING_OUTPUT_KIND}:
        normalized_payload = map_runtime_payload(payload)
        logger.info(
            "MEMORY_AGENT_RUNTIME_VALIDATION_DIAGNOSTIC %s",
            {
                "contract_kind": normalized,
                "payload_top_keys": summarize_top_level_keys(normalized_payload),
                "runtime_validation_ok": True,
            },
        )
    return True


def _extract_event_text_chunks(event: Any) -> list[str]:
    event_dict = event_to_dict(event)
    if not isinstance(event_dict, dict):
        return []
    out: list[str] = []
    _walk_for_text_chunks(event_dict.get("content"), out)
    _walk_for_text_chunks(event_dict.get("parts"), out)
    return out


def _walk_for_text_chunks(node: Any, out: list[str]) -> None:
    if node is None:
        return
    if isinstance(node, list):
        for item in node:
            _walk_for_text_chunks(item, out)
        return

    if isinstance(node, dict):
        text = node.get("text")
        if isinstance(text, str):
            out.append(text)
        if "parts" in node:
            _walk_for_text_chunks(node.get("parts"), out)


def get_contract_selector(contract_kind: str | None) -> Any:
    return resolve_contract_selector(contract_kind=contract_kind)


def resolve_contract_selector(*, contract_kind: str | None) -> Any:
    normalized = canonicalize_contract_kind(contract_kind)
    if normalized == MEMORY_DAILY_OUTPUT_KIND:
        return select_canonical_daily_memory_output_candidate
    if normalized == MEMORY_ROLLING_OUTPUT_KIND:
        return select_canonical_rolling_memory_output_candidate
    if normalized == REPLY_AGENT_OUTPUT_KIND:
        return select_canonical_reply_envelope_candidate
    raise ValueError(
        "contract routing violation: unknown contract_kind "
        f"'{contract_kind}'"
    )


def selector_mode_name(*, contract_kind: str | None) -> str:
    normalized = canonicalize_contract_kind(contract_kind)
    if normalized == REPLY_AGENT_OUTPUT_KIND:
        return "reply_envelope_contract"
    if normalized == MEMORY_DAILY_OUTPUT_KIND:
        return "memory_daily_contract_boundary_v1"
    if normalized == MEMORY_ROLLING_OUTPUT_KIND:
        return "memory_rolling_contract_boundary_v1"
    raise ValueError(
        "contract routing violation: unknown contract_kind "
        f"'{contract_kind}'"
    )


def is_memory_contract_kind(contract_kind: str | None) -> bool:
    normalized = canonicalize_contract_kind(contract_kind)
    return normalized in {MEMORY_DAILY_OUTPUT_KIND, MEMORY_ROLLING_OUTPUT_KIND}


def select_canonical_reply_envelope_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload")
    path = str(candidate.get("path") or "")
    depth = int(candidate.get("depth") or 0)
    if not isinstance(payload, dict):
        return {"is_valid": False, "reason": "payload_is_not_dict", "score": -1, "selector_rule": "payload_is_not_dict"}

    keys = set(payload.keys())
    if _SERVICE_ONLY_KEYS.intersection(keys) and keys != _CANONICAL_REPLY_KEYS:
        return {
            "is_valid": False,
            "reason": "service_keys_without_reply_contract",
            "score": 0,
            "selector_rule": "service_keys_without_reply_contract",
        }

    if keys != _CANONICAL_REPLY_KEYS:
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

    location_score = _location_score(path)
    score = location_score - depth
    return {
        "is_valid": True,
        "reason": f"canonical_reply_envelope@{_location_label(path)}",
        "score": score,
        "selector_rule": "canonical_reply_envelope",
    }


def select_canonical_daily_memory_output_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload")
    path = str(candidate.get("path") or "")
    depth = int(candidate.get("depth") or 0)
    if not isinstance(payload, dict):
        return {"is_valid": False, "reason": "payload_is_not_dict", "score": -1, "selector_rule": "payload_is_not_dict"}

    if _SERVICE_ONLY_KEYS.intersection(payload.keys()) or "result" in payload:
        return {
            "is_valid": False,
            "reason": _DAILY_CONTRACT_INVALID,
            "score": 0,
            "selector_rule": _DAILY_CONTRACT_INVALID,
        }
    try:
        DailyMemoryContract.model_validate(payload)
    except ValidationError:
        return {
            "is_valid": False,
            "reason": _DAILY_CONTRACT_INVALID,
            "score": 0,
            "selector_rule": _DAILY_CONTRACT_INVALID,
        }

    location_score = _location_score(path)
    score = location_score - depth
    return {
        "is_valid": True,
        "reason": f"{_DAILY_CONTRACT_INVALID}@ok:{_location_label(path)}",
        "score": score,
        "selector_rule": "daily_contract_valid",
    }




def select_canonical_rolling_memory_output_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    payload = candidate.get("payload")
    path = str(candidate.get("path") or "")
    depth = int(candidate.get("depth") or 0)
    if not isinstance(payload, dict):
        return {"is_valid": False, "reason": "payload_is_not_dict", "score": -1, "selector_rule": "payload_is_not_dict"}

    if _SERVICE_ONLY_KEYS.intersection(payload.keys()) or "result" in payload:
        return {
            "is_valid": False,
            "reason": _ROLLING_CONTRACT_INVALID,
            "score": 0,
            "selector_rule": _ROLLING_CONTRACT_INVALID,
        }
    try:
        RollingMemoryContract.model_validate(payload)
    except ValidationError:
        return {
            "is_valid": False,
            "reason": _ROLLING_CONTRACT_INVALID,
            "score": 0,
            "selector_rule": _ROLLING_CONTRACT_INVALID,
        }

    location_score = _location_score(path)
    score = location_score - depth
    return {
        "is_valid": True,
        "reason": f"{_ROLLING_CONTRACT_INVALID}@ok:{_location_label(path)}",
        "score": score,
        "selector_rule": "rolling_contract_valid",
    }

def _location_score(path: str) -> int:
    if ".output" in path:
        return 300
    if ".function_call.arguments" in path or ".function_call.args" in path:
        return 200
    if ".functionCall.arguments" in path or ".functionCall.args" in path:
        return 200
    return 100


def _location_label(path: str) -> str:
    if ".output" in path:
        return "top_level_output"
    if ".function_call.arguments" in path or ".function_call.args" in path:
        return "function_call_arguments"
    if ".functionCall.arguments" in path or ".functionCall.args" in path:
        return "functionCall_arguments"
    return "nested_misc_dict"


def summarize_top_level_keys(payload: dict[str, Any]) -> list[str]:
    return [str(key) for key in payload.keys()][:_KEY_PREVIEW_LIMIT]


def candidate_preview(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Provide non-sensitive candidate telemetry.
    Never includes raw values/text to avoid accidental PII leakage.
    """
    top_keys = summarize_top_level_keys(payload)
    nested_shape: dict[str, Any] = {}
    for key in top_keys[:_NESTED_KEY_PREVIEW_LIMIT]:
        value = payload.get(key)
        if isinstance(value, dict):
            nested_shape[key] = summarize_top_level_keys(value)
        elif isinstance(value, list):
            nested_shape[key] = f"list[{len(value)}]"
        else:
            nested_shape[key] = type(value).__name__
    return {
        "top_keys": top_keys,
        "top_key_count": len(payload),
        "nested_shape": nested_shape,
    }


def event_to_dict(event: Any) -> dict[str, Any] | None:
    if isinstance(event, dict):
        return event

    if hasattr(event, "to_dict"):
        dumped = event.to_dict()
        if isinstance(dumped, dict):
            return dumped

    if hasattr(event, "model_dump"):
        dumped = event.model_dump()
        if isinstance(dumped, dict):
            return dumped

    return None


def event_preview(event: Any) -> dict[str, Any]:
    event_dict = event_to_dict(event)
    if not isinstance(event_dict, dict):
        return {"event_type": type(event).__name__}

    return {
        "keys": list(event_dict.keys()),
        "has_output": isinstance(event_dict.get("output"), dict),
        "has_content_dict": isinstance(event_dict.get("content"), dict),
        "has_function_call": isinstance(event_dict.get("function_call"), dict) or isinstance(
            event_dict.get("functionCall"), dict),
    }
