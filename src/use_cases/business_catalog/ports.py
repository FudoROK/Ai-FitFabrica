"""Ports for business catalog persistence adapters."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductOffer,
    CatalogImportJob,
    CatalogImportRowError,
)
from src.domain.vector_search import VectorNamespace, VectorPointRecord
from src.use_cases.business_catalog.search_projection import BusinessCatalogSearchRecord


class BusinessCatalogRepositoryPort(Protocol):
    """Persistence boundary for seller-owned catalog data."""

    async def save_merchant(self, merchant: BusinessMerchant) -> BusinessMerchant:
        """Persist a merchant profile."""

    async def get_merchant_by_owner(self, owner_id: str) -> BusinessMerchant | None:
        """Return the merchant profile owned by one workspace owner."""

    async def save_product(self, product: BusinessProduct) -> BusinessProduct:
        """Persist product metadata."""

    async def get_product(self, product_id: str) -> BusinessProduct | None:
        """Return one product by id."""

    async def list_products(self, owner_id: str) -> list[BusinessProduct]:
        """Return products owned by one workspace owner."""

    async def save_product_image(self, image: BusinessProductImage) -> BusinessProductImage:
        """Persist product image metadata."""

    async def list_product_images(self, product_id: str) -> list[BusinessProductImage]:
        """Return images attached to one product."""

    async def save_offer(self, offer: BusinessProductOffer) -> BusinessProductOffer:
        """Persist product offer metadata."""

    async def get_offer(self, product_id: str) -> BusinessProductOffer | None:
        """Return sellable offer for one product, if present."""

    async def save_import_job(self, job: CatalogImportJob) -> CatalogImportJob:
        """Persist catalog import job metadata."""

    async def save_import_errors(self, errors: list[CatalogImportRowError]) -> None:
        """Persist row-level import validation errors."""

    async def list_approved_search_records(self, *, limit: int) -> list[BusinessCatalogSearchRecord]:
        """Return approved catalog products that are safe to index for public search."""

    async def list_approved_search_records_by_product_ids(self, *, product_ids: list[str]) -> list[BusinessCatalogSearchRecord]:
        """Return approved catalog search records for specific product ids."""

    async def mark_search_indexed(self, *, product_ids: list[str]) -> None:
        """Mark approved products as successfully indexed for search."""

    async def mark_search_index_failed(self, *, product_ids: list[str], reason: str) -> None:
        """Mark approved products as failed during search indexing."""


class BusinessCatalogFileStoragePort(Protocol):
    """Storage boundary for business catalog uploads."""

    async def save_upload(self, *, owner_id: str, filename: str, content_type: str, content: bytes) -> str:
        """Store an uploaded catalog or product media object and return its object key."""


class BusinessCatalogCategoryAnalysis(BaseModel):
    """Visual category analysis result for one catalog product image."""

    model_config = ConfigDict(extra="forbid")

    visual_category: str = Field(min_length=1, max_length=128)
    confidence: float = Field(ge=0.0, le=1.0)


class BusinessCatalogCategoryAnalysisPort(Protocol):
    """Backend-owned visual category analysis boundary."""

    async def analyze_product_image(
        self,
        *,
        job_id: str,
        object_key: str,
        content_type: str,
    ) -> BusinessCatalogCategoryAnalysis:
        """Analyze one stored product image and return visual category facts."""


class BusinessCatalogVectorIndexPort(Protocol):
    """Vector index boundary for approved business catalog search records."""

    def upsert_points(self, *, records: list[VectorPointRecord]) -> None:
        """Persist product vector points in the configured vector backend."""


class BusinessCatalogVectorBootstrapperPort(Protocol):
    """Vector collection bootstrap boundary for business catalog indexing."""

    def ensure_collection(self, *, namespace: VectorNamespace) -> None:
        """Ensure the vector collection for the namespace exists."""
