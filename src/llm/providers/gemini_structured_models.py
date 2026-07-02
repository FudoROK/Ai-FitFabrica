from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StructuredReasoningResult:
    """Lightweight structured reasoning result returned by the Gemini provider."""

    task: str
    payload: dict[str, Any]
    provider: str
    model: str
