from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RollingUpdate(StrictBaseModel):
    rolling_summary_text: str
    open_questions: list[str] = Field(default_factory=list)
    carry_forward_notes: list[str] = Field(default_factory=list)
    days_count: int
    last_daily_summary_date: str # Assuming ISO format date string
    version: int


class RollingMemoryContract(StrictBaseModel):
    rolling_update: RollingUpdate


__all__ = [
    "StrictBaseModel",
    "RollingUpdate",
    "RollingMemoryContract",
]
