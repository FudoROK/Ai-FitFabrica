"""Ports used by the similar-search workflow."""

from __future__ import annotations

from typing import Protocol

from src.domain.provider_models import EmbeddingRequest, EmbeddingResult
from src.domain.marketplace_search import MarketplaceConnectorExecutionReport, MarketplaceConnectorQuery
from src.domain.similar_search import (
    CatalogOfferRecord,
    CatalogProductRecord,
    HydratedCatalogMatch,
    SimilarSearchClickEvent,
    SimilarSearchClickAnalyticsResponse,
    SimilarityQueryProfile,
)
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


class SimilarSearchLocalCatalogSearchPort(Protocol):
    """Approved local catalog fallback used when vector search has no usable hits."""

    async def search_approved_matches(
        self,
        *,
        profile: SimilarityQueryProfile,
        limit: int,
    ) -> list[HydratedCatalogMatch]:
        """Return approved local catalog matches for one backend-owned search profile."""


class SimilarSearchMarketplaceConnectorPort(Protocol):
    """Approved external marketplace/search connector boundary.

    Implementations may call official APIs, partner feeds, seller-connected stores, or
    Instagram Business adapters. They must not perform hidden scraping.
    """

    async def search(self, *, query: MarketplaceConnectorQuery) -> MarketplaceConnectorExecutionReport:
        """Return one isolated connector execution report."""


class SimilarSearchClickEventRepositoryPort(Protocol):
    """Persistence boundary for free-search product interest events."""

    async def save_click_event(self, event: SimilarSearchClickEvent) -> SimilarSearchClickEvent:
        """Persist one similar-search click event."""

    async def get_click_analytics(self, *, limit: int) -> SimilarSearchClickAnalyticsResponse:
        """Return aggregate click analytics without exposing user-level events."""
