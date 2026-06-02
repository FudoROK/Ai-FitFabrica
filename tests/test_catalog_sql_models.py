from __future__ import annotations

from src.adapters.database.sql.catalog_models import MarketplaceOfferRow, ProductRow


def test_catalog_sql_models_define_product_and_offer_tables() -> None:
    assert ProductRow.__tablename__ == "products"
    assert MarketplaceOfferRow.__tablename__ == "marketplace_offers"
