"""Typed domain models for backend-owned pricing workflows."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PricingRequest(BaseModel):
    """Backend-owned request to build one pricing recommendation."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1)
    target_currency: str = Field(min_length=1)
    desired_margin_percent: float | None = Field(default=None, ge=0)


class PricingRecommendation(BaseModel):
    """Structured pricing recommendation returned by the backend."""

    model_config = ConfigDict(extra="forbid")

    recommended_price: float = Field(ge=0)
    currency: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    market_min: float = Field(ge=0)
    market_avg: float = Field(ge=0)
    market_max: float = Field(ge=0)


class PricingJobRecord(BaseModel):
    """Canonical persisted pricing job metadata."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    target_currency: str = Field(min_length=1)
    desired_margin_percent: float | None = Field(default=None, ge=0)
    status: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime


class PricingRecommendationRecord(BaseModel):
    """Persisted pricing recommendation bound to one pricing job."""

    model_config = ConfigDict(extra="forbid")

    recommendation_id: str = Field(min_length=1)
    job_id: str = Field(min_length=1)
    recommendation: PricingRecommendation
    created_at: datetime


class PricingComparable(BaseModel):
    """Comparable market evidence used to build one recommendation."""

    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(min_length=1)
    price_amount: float = Field(ge=0)
    currency: str = Field(min_length=1)
