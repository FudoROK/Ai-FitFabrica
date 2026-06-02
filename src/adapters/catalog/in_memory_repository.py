"""In-memory catalog repository for local similar-search fallbacks and tests."""

from __future__ import annotations

from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord
from src.use_cases.similar_search.ports import SimilarSearchCatalogRepositoryPort


class InMemoryCatalogRepository(SimilarSearchCatalogRepositoryPort):
    """Minimal in-memory catalog store for non-SQL environments."""

    def __init__(
        self,
        *,
        products: list[CatalogProductRecord] | None = None,
        offers: list[CatalogOfferRecord] | None = None,
    ) -> None:
        """Initialize an in-memory product and offer registry."""
        self._products = list(products or [])
        self._offers = list(offers or [])

    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]:
        """Return configured products matching the requested ids."""
        requested = set(product_ids)
        return [product for product in self._products if product.product_id in requested]

    async def list_offers_for_products(
        self,
        product_ids: list[str],
        *,
        marketplace_filters: list[str],
    ) -> list[CatalogOfferRecord]:
        """Return configured offers matching requested products and optional marketplaces."""
        requested_products = set(product_ids)
        requested_marketplaces = set(marketplace_filters)
        results = [offer for offer in self._offers if offer.product_id in requested_products]
        if requested_marketplaces:
            results = [offer for offer in results if offer.marketplace in requested_marketplaces]
        return results
