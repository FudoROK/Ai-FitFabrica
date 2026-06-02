"""Mapping helpers between SQL catalog rows and similar-search domain records."""

from __future__ import annotations

from src.domain.similar_search import CatalogOfferRecord, CatalogProductRecord

from .catalog_models import MarketplaceOfferRow, ProductRow


def product_record_from_row(row: ProductRow) -> CatalogProductRecord:
    """Convert a SQL product row into a domain catalog record."""
    return CatalogProductRecord(
        product_id=row.product_id,
        title=row.title,
        category=row.category,
        brand=row.brand,
        color=row.color,
    )


def offer_record_from_row(row: MarketplaceOfferRow) -> CatalogOfferRecord:
    """Convert a SQL offer row into a domain offer record."""
    return CatalogOfferRecord(
        offer_id=row.offer_id,
        product_id=row.product_id,
        marketplace=row.marketplace,
        price_amount=float(row.price_amount),
        currency=row.currency,
        product_url=row.product_url,
        is_available=row.is_available,
    )
