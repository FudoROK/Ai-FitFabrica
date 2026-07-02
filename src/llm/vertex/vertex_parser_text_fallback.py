"""Text-stream fallback extraction for Vertex structured outputs."""
from __future__ import annotations

import json
from typing import Any

from .vertex_parser_helpers import candidate_preview, extract_event_text_chunks, extract_json_object_candidates, normalize_streamed_text
from .vertex_parser_runtime_validation import validate_runtime_contract
from .vertex_parser_selectors import resolve_contract_selector


def collect_json_payload_from_text_chunks(
    *,
    events: list[Any],
    contract_kind: str | None,
    correlation_id: str | None,
) -> dict[str, Any] | None:
    """Extract a validated JSON payload from streamed text chunks."""

    chunks: list[str] = []
    for event in events:
        chunks.extend(extract_event_text_chunks(event))
    if not chunks:
        return None

    raw_payload = "".join(chunks).strip()
    if not raw_payload:
        return None

    normalized_payload = normalize_streamed_text(raw_payload)
    json_candidates = extract_json_object_candidates(normalized_payload)

    parsed_candidates: list[dict[str, Any]] = []
    for candidate_index, candidate_text in enumerate(json_candidates):
        try:
            parsed_payload = json.loads(candidate_text)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed_payload, dict):
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
        if not selection.get("is_valid"):
            continue
        if not validate_runtime_contract(contract_kind=contract_kind, payload=parsed_payload):
            continue
        return parsed_payload
    raise ValueError(
        "Vertex structured output extraction contract violation: extraction/invalid_output in streamed text chunks"
    )
