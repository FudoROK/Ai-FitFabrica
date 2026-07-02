from __future__ import annotations

import logging
from typing import Any

from ..contract_kinds import (
    REPLY_AGENT_OUTPUT_KIND,
)
from ..transport.structured_extractor import collect_raw_structured_payload_candidates
from .vertex_parser_helpers import candidate_preview, event_preview
from .vertex_parser_selectors import (
    resolve_contract_selector,
)
from .vertex_parser_text_fallback import collect_json_payload_from_text_chunks

logger = logging.getLogger(__name__)


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
        for candidate in collect_raw_structured_payload_candidates(event, event_index=event_index):
            candidate_count += 1
            selection = selector(candidate)

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
        chunk_payload = collect_json_payload_from_text_chunks(
            events=events,
            contract_kind=contract_kind,
            correlation_id=correlation_id,
        )
        if chunk_payload is not None:
            return {
                "output": chunk_payload,
                "event_count": len(events),
            }
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

    return {
        "output": payload,
        "event_count": len(events),
    }


def get_contract_selector(contract_kind: str | None) -> Any:
    return resolve_contract_selector(contract_kind=contract_kind)
