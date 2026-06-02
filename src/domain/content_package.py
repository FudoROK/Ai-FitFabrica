"""Typed domain models for backend-owned content-package workflows."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ContentPackageRequest(BaseModel):
    """Backend-owned request to generate one content package."""

    model_config = ConfigDict(extra="forbid")

    product_card_version_id: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    requested_channels: list[str] = Field(default_factory=list)


class ContentPackageOption(BaseModel):
    """One generated content-package asset descriptor."""

    model_config = ConfigDict(extra="forbid")

    asset_kind: str = Field(min_length=1)
    label: str = Field(min_length=1)


class ContentPackageJobRecord(BaseModel):
    """Canonical persisted content-package job metadata."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    product_card_version_id: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    status: str = Field(min_length=1)
    requested_channels: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ContentPackageVersionRecord(BaseModel):
    """Persisted generated content-package version metadata."""

    model_config = ConfigDict(extra="forbid")

    version_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    assets: list[ContentPackageOption] = Field(default_factory=list)
    created_at: datetime
