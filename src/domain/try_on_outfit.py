"""Domain models for Try-On outfit composition validation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class TryOnOutfitCompositionDecision(StrEnum):
    """Deterministic backend decision for an outfit slot combination."""

    ALLOW = "allow"
    BLOCK = "block"
    REQUEST_BETTER_INPUT = "request_better_input"


class TryOnOutfitCompositionVerdict(BaseModel):
    """Structured result of validating a garment slot combination."""

    model_config = ConfigDict(extra="forbid")

    decision: TryOnOutfitCompositionDecision
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
