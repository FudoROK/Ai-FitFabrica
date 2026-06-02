"""SQL-backed repositories for similar-search catalog hydration."""

from __future__ import annotations

from sqlalchemy import select

from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord
from src.use_cases.similar_search.ports import SimilarSearchCatalogRepositoryPort

from .catalog_models import MarketplaceOfferRow, ProductRow
from .catalog_serialization import offer_record_from_row, product_record_from_row


class SqlCatalogRepository(SimilarSearchCatalogRepositoryPort):
    """Hydrate products and offers from the portable SQL catalog."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared async session factory."""
        self._session_factory = session_factory

    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]:
        """Return canonical products for the requested ids."""
        if not product_ids:
            return []
        async with self._session_factory() as session:
            rows = (await session.scalars(select(ProductRow).where(ProductRow.product_id.in_(product_ids)))).all()
            return [product_record_from_row(row) for row in rows]

    async def list_offers_for_products(
        self,
        product_ids: list[str],
        *,
        marketplace_filters: list[str],
    ) -> list[CatalogOfferRecord]:
        """Return marketplace offers for the requested products, filtered when requested."""
        if not product_ids:
            return []
        async with self._session_factory() as session:
            query = select(MarketplaceOfferRow).where(MarketplaceOfferRow.product_id.in_(product_ids))
            if marketplace_filters:
                query = query.where(MarketplaceOfferRow.marketplace.in_(marketplace_filters))
            rows = (await session.scalars(query)).all()
            return [offer_record_from_row(row) for row in rows]
