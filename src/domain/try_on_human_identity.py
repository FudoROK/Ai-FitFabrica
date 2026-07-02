"""Human Identity analysis domain models owned by the Try-On workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


class TryOnHumanIdentityVerdict(StrEnum):
    """Backend-owned continuation verdict for human identity analysis."""

    ALLOWED = "allowed"
    BLOCKED = "blocked"


class TryOnHumanIdentityPolicyDecision(BaseModel):
    """Fail-closed backend decision derived from validated human analysis."""

    model_config = ConfigDict(extra="forbid")

    verdict: TryOnHumanIdentityVerdict
    rejection_reasons: list[str] = Field(default_factory=list)


class TryOnHumanIdentityPreservationTarget(BaseModel):
    """One approved human attribute that generation must preserve."""

    model_config = ConfigDict(extra="forbid")

    attribute_name: str = Field(min_length=1)
    preservation_reason: str = Field(min_length=1)


class TryOnHumanIdentityEvidence(BaseModel):
    """Safe evidence metadata copied from validated agent output."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class TryOnHumanIdentityAnalysis(BaseModel):
    """Validated and policy-evaluated Human Identity snapshot for one Try-On job."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    face_visibility: Literal["fully_visible", "partially_visible", "occluded", "not_visible"]
    pose_summary: str = Field(min_length=1)
    body_region_visibility: list[str] = Field(default_factory=list)
    subject_count: int = Field(default=1, ge=0)
    crop_quality: Literal["full_body", "upper_body", "headshot", "extreme_crop"] = "upper_body"
    try_on_body_coverage: Literal["sufficient", "partial", "insufficient"] = "partial"
    occlusion_risk: Literal["low", "medium", "high"] = "medium"
    required_regions_missing: list[str] = Field(default_factory=list)
    preservation_targets: list[TryOnHumanIdentityPreservationTarget] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence: list[TryOnHumanIdentityEvidence] = Field(default_factory=list)
    uncertainty_level: Literal["low", "medium", "high"]
    unknowns: list[str] = Field(default_factory=list)
    verdict: TryOnHumanIdentityVerdict
    rejection_reasons: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=utc_now)
