from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from .types import LLMError, ToolCall, Usage


@dataclass(frozen=True)
class LLMResult:
    status: str
    text: Optional[str] = None
    structured_data: Optional[dict[str, Any]] = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    provider: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    retry_count: int = 0
    usage: Optional[Usage] = None
    error: Optional[LLMError] = None
    provider_metadata: dict[str, Any] = field(default_factory=dict)
