"""Workflow-facing ports and models for pricing orchestration."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from src.domain.pricing import (
    PricingComparable,
    PricingJobRecord,
    PricingRecommendation,
    PricingRecommendationRecord,
    PricingRequest,
)


class PricingBrief(BaseModel):
    """Backend-owned pricing brief prepared before comparable lookup starts."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1)
    target_currency: str = Field(min_length=1)
    desired_margin_percent: float | None = Field(default=None, ge=0)


class PricingRepositoryPort(Protocol):
    """Port for durable pricing workflow persistence."""

    async def create_job(self, *, request: PricingRequest, now) -> PricingJobRecord:
        """Create one durable pricing job."""

    async def save_recommendation(
        self,
        *,
        job_id: str,
        recommendation: PricingRecommendation,
        now,
    ) -> PricingRecommendationRecord:
        """Persist one structured pricing recommendation."""

    async def get_job(self, job_id: str) -> PricingJobRecord | None:
        """Return the persisted pricing job for the requested identifier."""

    async def get_latest_recommendation(self, job_id: str) -> PricingRecommendationRecord | None:
        """Return the latest structured pricing recommendation for the requested job."""

    async def mark_completed(self, job_id: str, *, now) -> PricingJobRecord:
        """Mark the requested pricing job as completed."""


class PricingComparisonSourcePort(Protocol):
    """Port for fetching comparable market evidence."""

    async def list_comparables(self, brief: PricingBrief) -> list[PricingComparable]:
        """Return comparable market evidence for the requested pricing brief."""
