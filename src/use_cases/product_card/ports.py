"""Workflow-facing ports for product-card orchestration."""

from __future__ import annotations

from typing import Protocol

from src.domain.product_card import (
    ProductCardDraft,
    ProductCardGarmentAnalysis,
    ProductCardJobRecord,
    ProductCardRequest,
    ProductCardVersionRecord,
)

from .workflow_service import ProductCardSourceFile


class ProductCardFileStoragePort(Protocol):
    """Port for persisting source assets before generation starts."""

    async def store_many(self, *, source_files: list[ProductCardSourceFile]) -> list[str]:
        """Persist all source files and return their object keys."""


class ProductCardRepositoryPort(Protocol):
    """Port for durable product-card workflow persistence."""

    async def create_job(
        self,
        *,
        request: ProductCardRequest,
        asset_keys: list[str],
        now,
    ) -> ProductCardJobRecord:
        """Create one durable product-card job."""

    async def save_generated_version(
        self,
        *,
        job_id: str,
        draft: ProductCardDraft,
        now,
    ) -> ProductCardVersionRecord:
        """Persist one generated product-card version."""

    async def save_garment_analysis(self, analysis: ProductCardGarmentAnalysis) -> ProductCardGarmentAnalysis:
        """Persist one validated reusable garment analysis."""

    async def get_garment_analysis(self, job_id: str) -> ProductCardGarmentAnalysis | None:
        """Return the saved garment analysis for one Product Card job."""

    async def mark_completed(self, job_id: str, *, now) -> ProductCardJobRecord:
        """Mark the job as completed and return the updated job record."""

    async def mark_failed(self, job_id: str, *, now) -> ProductCardJobRecord:
        """Mark the job as failed and return the updated job record."""

    async def get_job(self, job_id: str) -> ProductCardJobRecord | None:
        """Return the persisted job for the requested identifier."""

    async def get_latest_version(self, job_id: str) -> ProductCardVersionRecord | None:
        """Return the latest generated version for the requested job."""

    async def list_recent(self, *, limit: int) -> list[ProductCardJobRecord]:
        """Return recent product-card jobs for workspace history surfaces."""


class ProductCardGenerationPort(Protocol):
    """Port for provider-neutral product-card draft generation."""

    async def generate(
        self,
        *,
        request: ProductCardRequest,
        garment_analysis: ProductCardGarmentAnalysis,
    ) -> ProductCardDraft:
        """Generate one structured product-card draft."""


class GarmentIdentityAnalysisPort(Protocol):
    """Port for provider-neutral garment identity analysis."""

    async def analyze(self, *, job_id: str, asset_keys: list[str]) -> ProductCardGarmentAnalysis:
        """Return one validated reusable garment analysis."""
