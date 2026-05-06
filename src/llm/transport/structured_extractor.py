from __future__ import annotations

from typing import Any

_MAX_DEPTH = 5
_CONTAINER_KEYS = (
    "output",
    "content",
    "parts",
    "payload",
    "data",
    "result",
    "response",
    "value",
    "function_call",
    "functionCall",
    "function_response",
    "functionResponse",
    "args",
    "arguments",
)


def collect_raw_structured_payload_candidates(event: Any, *, event_index: int) -> list[dict[str, Any]]:
    """Collect raw payload candidates with traversal metadata for one provider event."""
    event_dict = _to_dict(event)
    if not isinstance(event_dict, dict):
        return []

    candidates: list[dict[str, Any]] = []
    _walk(event_dict, path="event", depth=0, event_index=event_index, out=candidates)
    return candidates


def extract_raw_structured_payload(event: Any) -> dict[str, Any] | None:
    """Return the last raw structured payload found in one provider event."""
    candidates = collect_raw_structured_payload_candidates(event, event_index=0)
    if not candidates:
        return None
    payload = candidates[-1].get("payload")
    return payload if isinstance(payload, dict) else None


def _walk(value: Any, *, path: str, depth: int, event_index: int, out: list[dict[str, Any]]) -> None:
    if depth > _MAX_DEPTH:
        return

    mapping = _to_dict(value)
    if isinstance(mapping, dict):
        value = mapping

    if isinstance(value, dict):
        for key in _CONTAINER_KEYS:
            nested = value.get(key)
            if nested is None:
                continue
            nested_path = f"{path}.{key}"
            _collect_candidate(nested, path=nested_path, depth=depth + 1, event_index=event_index, out=out)
            _walk(nested, path=nested_path, depth=depth + 1, event_index=event_index, out=out)
        return

    if isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]"
            _collect_candidate(item, path=item_path, depth=depth + 1, event_index=event_index, out=out)
            _walk(item, path=item_path, depth=depth + 1, event_index=event_index, out=out)


def _collect_candidate(value: Any, *, path: str, depth: int, event_index: int, out: list[dict[str, Any]]) -> None:
    mapping = _to_dict(value)
    if not isinstance(mapping, dict):
        return
    for candidate in out:
        if candidate.get("payload") is mapping:
            return
    out.append(
        {
            "payload": mapping,
            "path": path,
            "depth": depth,
            "event_index": event_index,
        }
    )


def _to_dict(value: Any) -> dict[str, Any] | None:
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
