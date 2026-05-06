from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ExtractionStatus = Literal["success", "partial", "failed"]
ExtractionAttempt = Literal["strict", "soft", "quarantine"]


class ExtractionResult(BaseModel):
    status: ExtractionStatus
    data: dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    missing: list[str] = Field(default_factory=list)
    error_type: str | None = None
    raw_response: str | None = None
    provider: str | None = None
    task_name: str
    schema_version: str = "v1"
    attempt: ExtractionAttempt
