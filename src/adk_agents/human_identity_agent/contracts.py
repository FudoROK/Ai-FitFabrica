"""Typed contracts for the FitFabrica human identity agent."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from src.domain.image_agent_contracts import AgentEvidence, SafeBackendFactsModel, StrictImageAgentModel, UncertaintyLevel


class HumanIdentityRequest(SafeBackendFactsModel):
    """Backend-approved request for human preservation analysis."""

    human_photo_object_key: str = Field(min_length=1)
    requested_checks: list[Literal["face_visibility", "pose", "body_regions", "lighting", "background"]] = Field(
        default_factory=lambda: ["face_visibility", "pose", "body_regions", "lighting", "background"],
        min_length=1,
    )


class HumanIdentityPreservationTarget(StrictImageAgentModel):
    """One human attribute that the backend must preserve during image workflows."""

    attribute_name: str = Field(min_length=1)
    preservation_reason: str = Field(min_length=1)


class HumanIdentityContract(StrictImageAgentModel):
    """Structured human-identity facts required by backend-owned Try-On orchestration."""

    face_visibility: Literal["fully_visible", "partially_visible", "occluded", "not_visible"]
    pose_summary: str = Field(min_length=1)
    body_region_visibility: list[str] = Field(default_factory=list)
    subject_count: int = Field(ge=0)
    crop_quality: Literal["full_body", "upper_body", "headshot", "extreme_crop"]
    try_on_body_coverage: Literal["sufficient", "partial", "insufficient"]
    occlusion_risk: Literal["low", "medium", "high"]
    required_regions_missing: list[str] = Field(default_factory=list)
    preservation_targets: list[HumanIdentityPreservationTarget] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    evidence: list[AgentEvidence] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.LOW
    unknowns: list[str] = Field(default_factory=list)
