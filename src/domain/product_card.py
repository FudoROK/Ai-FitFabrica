"""Typed domain models for backend-owned product-card workflows."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    """Return the current timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class ProductCardGarmentVisualDetail(BaseModel):
    """One validated visual garment detail reusable by backend workflows."""

    model_config = ConfigDict(extra="forbid")

    detail_type: str = Field(min_length=1)
    description: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class ProductCardGarmentEvidence(BaseModel):
    """One safe evidence item supporting a persisted garment conclusion."""

    model_config = ConfigDict(extra="forbid")

    source_type: str = Field(min_length=1)
    source_ref: str = Field(min_length=1)
    observation: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class ProductCardGarmentAnalysis(BaseModel):
    """Validated reusable Garment Identity snapshot for one Product Card job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
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
    confidence: float = Field(ge=0.0, le=1.0)
    limitations: list[str] = Field(default_factory=list)
    visual_details: list[ProductCardGarmentVisualDetail] = Field(default_factory=list)
    evidence: list[ProductCardGarmentEvidence] = Field(default_factory=list)
    uncertainty_level: str = Field(min_length=1)
    unknowns: list[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=utc_now)


class ProductCardRequest(BaseModel):
    """Backend-owned request to generate one product-card draft."""

    model_config = ConfigDict(extra="forbid")

    title_hint: str | None = None
    category: str = Field(default="uncategorized", min_length=1)
    target_channel: str = Field(min_length=1)
    brand_tone: str = Field(min_length=1)
    source_image_keys: list[str] = Field(default_factory=list)


class ProductCardDraft(BaseModel):
    """Structured draft content for one product-card version."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    bullet_points: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)


class ProductCardJobRecord(BaseModel):
    """Canonical persisted product-card job metadata."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    category: str = Field(default="uncategorized", min_length=1)
    target_channel: str = Field(min_length=1)
    brand_tone: str = Field(min_length=1)
    title_hint: str | None = None
    asset_keys: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ProductCardVersionRecord(BaseModel):
    """Persisted generated product-card version metadata."""

    model_config = ConfigDict(extra="forbid")

    version_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    bullet_points: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)
    created_at: datetime
