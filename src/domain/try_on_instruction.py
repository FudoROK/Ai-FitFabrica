"""Validated generation instruction produced from approved Try-On analyses."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class TryOnInstructionVerdict(StrEnum):
    """Backend-owned continuation verdict for Try-On generation instructions."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


class TryOnInstructionPolicyDecision(BaseModel):
    """Fail-closed backend decision derived from a validated instruction."""

    model_config = ConfigDict(extra="forbid")

    verdict: TryOnInstructionVerdict
    rejection_reasons: list[str] = Field(default_factory=list)


class TryOnGenerationInstruction(BaseModel):
    """Persistable instruction consumed by a backend-owned generation adapter."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    instruction_summary: str = Field(min_length=1)
    preserve_face: bool = True
    preserve_body_shape: bool = True
    preserve_pose: bool = True
    garment_focus_points: list[str] = Field(default_factory=list)
    outfit_slot_focus_points: list["TryOnOutfitSlotInstruction"] = Field(default_factory=list)
    styling_focus_points: list[str] = Field(default_factory=list)
    generation_exclusions: list[str] = Field(default_factory=list)
    expected_framing: str | None = None
    evidence: list[dict[str, object]] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    uncertainty_level: str = Field(min_length=1)
    completed_at: datetime = Field(default_factory=utc_now)


class TryOnOutfitSlotInstruction(BaseModel):
    """Generation constraints for one garment slot in a multi-garment outfit."""

    model_config = ConfigDict(extra="forbid")

    slot_role: str = Field(min_length=1)
    garment_type: str = Field(min_length=1)
    focus_points: list[str] = Field(default_factory=list)
    generation_exclusions: list[str] = Field(default_factory=list)
