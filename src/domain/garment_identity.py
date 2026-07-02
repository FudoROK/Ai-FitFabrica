"""Backend-owned policy models for Garment Identity analysis."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class GarmentIdentityWorkflowMode(StrEnum):
    """Supported workflow contexts for garment continuation policy."""

    PRODUCT_CARD = "product_card"
    TRY_ON = "try_on"


class GarmentIdentityVerdict(StrEnum):
    """Backend-owned continuation verdict for garment identity analysis."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


class GarmentIdentityPolicyDecision(BaseModel):
    """Fail-closed backend decision derived from validated garment analysis."""

    model_config = ConfigDict(extra="forbid")

    verdict: GarmentIdentityVerdict
    rejection_reasons: list[str] = Field(default_factory=list)
