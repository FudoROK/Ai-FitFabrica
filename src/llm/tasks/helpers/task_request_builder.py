from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from ...llm_base_contracts import LLMMeta
from ...core.request import LLMRequest
from ...core.result import LLMResult as CoreLLMResult


@dataclass
class ProviderRequestParts:
    model: str
    instructions: str
    input: str
    context: dict[str, Any] = field(default_factory=dict)
    structured_output: Optional[dict[str, Any]] = None
    tool_capabilities: list[dict[str, Any]] = field(default_factory=list)
    provider_metadata: dict[str, Any] = field(default_factory=dict)


def maybe_parse_json(value: Any) -> Optional[dict[str, Any]]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return None
    candidate = value.strip()
    if not candidate.startswith("{"):
        return None
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


def provider_parts_to_core_request(parts: ProviderRequestParts, *, task: str, meta: LLMMeta, max_retries: int = 1) -> LLMRequest:
    metadata: dict[str, Any] = {
        "trace_id": meta.trace_id,
        "message_id": meta.message_id,
        "lead_id": meta.lead_id,
        "channel": meta.channel,
        "delivery_id": meta.delivery_id,
        "instructions": parts.instructions,
    }

    return LLMRequest(
        task=task,
        input=parts.input,
        context=parts.context,
        structured_output=parts.structured_output,
        tool_capabilities=parts.tool_capabilities,
        model=parts.model,
        metadata=metadata,
        provider_metadata=parts.provider_metadata,
        max_retries=max_retries,
    )


def ensure_ok_result(result: CoreLLMResult) -> CoreLLMResult:
    if result.status == "ok":
        return result
    error_type = result.error.type if result.error else "unknown"
    message = result.error.message_redacted if result.error else "llm error"
    raise ValueError(f"{error_type}: {message}")
