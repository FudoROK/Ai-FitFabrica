from __future__ import annotations

from typing import Any

from pydantic import Field

from .base import StrictContractModel


class RollingUpdatePayload(StrictContractModel):
    rolling_summary_text: str
    open_questions: list[str] = Field(default_factory=list)
    carry_forward_notes: list[str] = Field(default_factory=list)
    days_count: int = Field(..., ge=1)
    last_daily_summary_date: str
    version: int = Field(..., ge=1)


class RollingMemoryInputContract(StrictContractModel):
    prior_rolling_memory: dict[str, Any] = Field(default_factory=dict)
    new_daily_summary: dict[str, Any] = Field(default_factory=dict)


class RollingMemoryContract(StrictContractModel):
    rolling_update: RollingUpdatePayload


__all__ = [
    "RollingUpdatePayload",
    "RollingMemoryInputContract",
    "RollingMemoryContract",
]
