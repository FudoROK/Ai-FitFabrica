"""Helper utilities for Vertex event parsing and non-sensitive previews."""
from __future__ import annotations

from typing import Any

KEY_PREVIEW_LIMIT = 12
NESTED_KEY_PREVIEW_LIMIT = 4


def summarize_top_level_keys(payload: dict[str, Any]) -> list[str]:
    return [str(key) for key in payload.keys()][:KEY_PREVIEW_LIMIT]


def candidate_preview(payload: dict[str, Any]) -> dict[str, Any]:
    top_keys = summarize_top_level_keys(payload)
    nested_shape: dict[str, Any] = {}
    for key in top_keys[:NESTED_KEY_PREVIEW_LIMIT]:
        value = payload.get(key)
        if isinstance(value, dict):
            nested_shape[key] = summarize_top_level_keys(value)
        elif isinstance(value, list):
            nested_shape[key] = f"list[{len(value)}]"
        else:
            nested_shape[key] = type(value).__name__
    return {"top_keys": top_keys, "top_key_count": len(payload), "nested_shape": nested_shape}


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
        "has_function_call": isinstance(event_dict.get("function_call"), dict)
        or isinstance(event_dict.get("functionCall"), dict),
    }


def extract_event_text_chunks(event: Any) -> list[str]:
    event_dict = event_to_dict(event)
    if not isinstance(event_dict, dict):
        return []
    out: list[str] = []
    _walk_for_text_chunks(event_dict.get("content"), out)
    _walk_for_text_chunks(event_dict.get("parts"), out)
    return out


def normalize_streamed_text(raw_payload: str) -> str:
    return raw_payload.replace("```json", "").replace("```JSON", "").replace("```", "").strip()


def extract_json_object_candidates(text: str) -> list[str]:
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
                candidates.append(text[start_index : idx + 1])
                start_index = None
            continue
    return candidates


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
