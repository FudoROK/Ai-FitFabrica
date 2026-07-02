"""Typed contracts for the FitFabrica garment identity agent."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from src.domain.image_agent_contracts import AgentEvidence, SafeBackendFactsModel, StrictImageAgentModel, UncertaintyLevel


class GarmentIdentityRequest(SafeBackendFactsModel):
    """Backend-approved request for garment identity analysis."""

    garment_photo_object_key: str = Field(min_length=1)
    trusted_product_facts: list[str] = Field(default_factory=list)


class GarmentVisualDetail(StrictImageAgentModel):
    """One visual garment detail that generation must preserve."""

    detail_type: Literal["collar", "sleeve", "pocket", "button", "closure", "print", "logo", "trim", "seam", "other"]
    description: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class GarmentWearControlCandidate(StrictImageAgentModel):
    """One backend-reviewable wear-control suggestion from garment analysis."""

    control_code: str = Field(min_length=1)
    recommended: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str | None = None
    risk: str | None = None


class UnknownGarmentTaxonomyCandidate(StrictImageAgentModel):
    """One new garment taxonomy candidate that requires human admin review."""

    proposed_code: str = Field(min_length=1)
    proposed_display_name: str = Field(min_length=1)
    proposed_category: str = Field(min_length=1)
    proposed_controls: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    agent_reasoning_summary: str = Field(min_length=1)


class GarmentIdentityContract(StrictImageAgentModel):
    """Structured garment facts that the backend must preserve or compare."""

    garment_type: str = Field(min_length=1)
    taxonomy_parent: str | None = None
    taxonomy_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    wear_control_candidates: list[GarmentWearControlCandidate] = Field(default_factory=list)
    unknown_taxonomy_candidate: UnknownGarmentTaxonomyCandidate | None = None
    garment_count: int = Field(default=1, ge=0)
    target_garment_index: int | None = Field(default=1, ge=1)
    target_garment_description: str | None = None
    garment_visibility: Literal["fully_visible", "mostly_visible", "partially_visible", "not_visible"] = "mostly_visible"
    crop_quality: Literal["full_garment", "minor_crop", "major_crop", "extreme_crop"] = "minor_crop"
    try_on_garment_coverage: Literal["sufficient", "partial", "insufficient"] = "partial"
    product_card_coverage: Literal["sufficient", "partial", "insufficient"] = "partial"
    occlusion_risk: Literal["low", "medium", "high"] = "medium"
    required_regions_missing: list[str] = Field(default_factory=list)
    ambiguous_target: bool = False
    dominant_color: str = Field(min_length=1)
    secondary_colors: list[str] = Field(default_factory=list)
    silhouette_summary: str = Field(min_length=1)
    preserved_details: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    visual_details: list[GarmentVisualDetail] = Field(default_factory=list)
    evidence: list[AgentEvidence] = Field(default_factory=list)
    uncertainty_level: UncertaintyLevel = UncertaintyLevel.LOW
    unknowns: list[str] = Field(default_factory=list)
