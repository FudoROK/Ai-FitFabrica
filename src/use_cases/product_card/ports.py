"""Workflow-facing ports for product-card orchestration."""

from __future__ import annotations

from typing import Protocol

from src.domain.product_card import (
    ProductCardDraft,
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

    async def mark_completed(self, job_id: str, *, now) -> ProductCardJobRecord:
        """Mark the job as completed and return the updated job record."""


class ProductCardGenerationPort(Protocol):
    """Port for provider-neutral product-card draft generation."""

    async def generate(
        self,
        *,
        request: ProductCardRequest,
        asset_keys: list[str],
    ) -> ProductCardDraft:
        """Generate one structured product-card draft."""
