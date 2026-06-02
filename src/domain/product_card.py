"""Typed domain models for backend-owned product-card workflows."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCardRequest(BaseModel):
    """Backend-owned request to generate one product-card draft."""

    model_config = ConfigDict(extra="forbid")

    title_hint: str | None = None
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
