"""Persisted garment and material analysis snapshots for Try-On workflows."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class TryOnAnalysisEvidence(BaseModel):
    """One safe evidence item supporting a Try-On analysis conclusion."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class TryOnGarmentVisualDetail(BaseModel):
    """One garment detail that generation must preserve."""

    model_config = ConfigDict(extra="forbid")

    detail_type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class TryOnGarmentIdentityAnalysis(BaseModel):
    """Validated Garment Identity snapshot owned by one Try-On job."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    garment_type: str = Field(min_length=1)
    taxonomy_parent: str | None = None
    taxonomy_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    wear_control_candidates: list[dict[str, object]] = Field(default_factory=list)
    unknown_taxonomy_candidate: dict[str, object] | None = None
    garment_count: int = Field(default=1, ge=0)
    target_garment_index: int | None = Field(default=1, ge=1)
    target_garment_description: str | None = None
    garment_visibility: str = Field(default="mostly_visible", min_length=1)
    crop_quality: str = Field(default="minor_crop", min_length=1)
    try_on_garment_coverage: str = Field(default="partial", min_length=1)
    product_card_coverage: str = Field(default="partial", min_length=1)
    occlusion_risk: str = Field(default="medium", min_length=1)
    required_regions_missing: list[str] = Field(default_factory=list)
    ambiguous_target: bool = False
    dominant_color: str = Field(min_length=1)
    secondary_colors: list[str] = Field(default_factory=list)
    silhouette_summary: str = Field(min_length=1)
    preserved_details: list[str] = Field(default_factory=list)
    visual_details: list[TryOnGarmentVisualDetail] = Field(default_factory=list)
    evidence: list[TryOnAnalysisEvidence] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    uncertainty_level: str = Field(min_length=1)
    unknowns: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=utc_now)


class TryOnGarmentSlotIdentityAnalysis(BaseModel):
    """Garment Identity analysis bound to one uploaded outfit slot."""

    model_config = ConfigDict(extra="forbid")

    slot_role: str = Field(min_length=1)
    analysis: TryOnGarmentIdentityAnalysis


class TryOnMaterialObservation(BaseModel):
    """One visible material behavior observation."""

    model_config = ConfigDict(extra="forbid")

    signal_type: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class TryOnMaterialTextureAnalysis(BaseModel):
    """Validated Material / Texture snapshot owned by one Try-On job."""

    model_config = ConfigDict(extra="forbid")

    invocation_id: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    contract_version: str = Field(min_length=1)
    visible_material_signals: list[str] = Field(default_factory=list)
    texture_signals: list[str] = Field(default_factory=list)
    evidence_note: str = Field(min_length=1)
    observations: list[TryOnMaterialObservation] = Field(default_factory=list)
    evidence: list[TryOnAnalysisEvidence] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    composition_status: str = Field(min_length=1, default="unknown")
    uncertainty_level: str = Field(min_length=1)
    alternative_interpretations: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=utc_now)
