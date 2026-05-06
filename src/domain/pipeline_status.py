"""Shared pipeline status model for runtime observability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


PipelineStatus = Literal["success", "degraded", "partial", "failed"]


@dataclass
class PipelineResult:
    """Lightweight status/result contract used across critical runtime paths."""

    status: PipelineStatus
    reply_text: Optional[str] = None
    error_type: Optional[str] = None

