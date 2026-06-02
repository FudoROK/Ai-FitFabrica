"""Ports used by the similar-search workflow."""

from __future__ import annotations

from typing import Protocol

from src.domain.provider_models import EmbeddingRequest, EmbeddingResult
from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord
from src.domain.vector_search import VectorSearchHit, VectorSearchQuery


class SimilarSearchEmbeddingPort(Protocol):
    """Embedding boundary used to convert query text into retrieval vectors."""

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Return an embedding for the prepared search query."""


class SimilarSearchCatalogRepositoryPort(Protocol):
    """Catalog hydration boundary used after vector retrieval."""

    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]:
        """Return canonical products for the requested identifiers."""

    async def list_offers_for_products(
        self,
        product_ids: list[str],
        *,
        marketplace_filters: list[str],
    ) -> list[CatalogOfferRecord]:
        """Return marketplace offers for the requested products."""


class SimilarSearchVectorRetrieverPort(Protocol):
    """Vector retrieval boundary used by the workflow service."""

    def search(self, *, query: VectorSearchQuery) -> list[VectorSearchHit]:
        """Return typed hits for the search query."""
