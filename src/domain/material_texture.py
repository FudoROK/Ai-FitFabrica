"""Backend-owned policy models for Material / Texture analysis."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MaterialTextureVerdict(StrEnum):
    """Backend-owned continuation verdict for material analysis."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


class MaterialTexturePolicyDecision(BaseModel):
    """Fail-closed backend decision derived from validated material analysis."""

    model_config = ConfigDict(extra="forbid")

    verdict: MaterialTextureVerdict
    rejection_reasons: list[str] = Field(default_factory=list)
