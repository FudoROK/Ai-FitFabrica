"""Pure context assembler for LLM runtime payloads."""
from __future__ import annotations

from typing import Any

from .context_projection import ContextProjection


def assemble_core_context_payload(projection: ContextProjection) -> dict[str, Any]:
    """Builds the final context payload from normalized projection data only."""
    return {
        "identity": projection.identity,
        "lead_snapshot": projection.lead_snapshot,
        "memory": {
            "rolling_summary": projection.memory.get("rolling_summary"),
            "daily_summary": projection.memory.get("daily_summary"),
            "last_messages": list(projection.memory.get("messages") or []),
        },
    }
