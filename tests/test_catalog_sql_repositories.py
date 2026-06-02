from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.catalog_models import MarketplaceOfferRow, ProductRow
from src.adapters.database.sql.catalog_repositories import SqlCatalogRepository


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.mark.asyncio
async def test_catalog_repository_returns_products_for_retrieved_owner_ids() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        session.add(
            ProductRow(
                product_id="product-1",
                title="Black midi dress",
                category="dress",
                brand="zara",
                color="black",
                created_at=_utc_now(),
                updated_at=_utc_now(),
            )
        )
        session.add(
            MarketplaceOfferRow(
                offer_id="offer-1",
                product_id="product-1",
                marketplace="lamoda",
                price_amount=Decimal("99.00"),
                currency="USD",
                product_url="https://example.test/offer-1",
                is_available=True,
                created_at=_utc_now(),
                updated_at=_utc_now(),
            )
        )
        await session.commit()

    repository = SqlCatalogRepository(session_factory=session_factory)
    products = await repository.get_products_by_ids(["product-1"])
    offers = await repository.list_offers_for_products(["product-1"], marketplace_filters=["lamoda"])

    assert products[0].product_id == "product-1"
    assert offers[0].offer_id == "offer-1"

    await engine.dispose()
