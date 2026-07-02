from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.business_catalog_repositories import SqlBusinessCatalogRepository
from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessMerchantStatus,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductOffer,
    BusinessProductStatus,
    CatalogImportJob,
    CatalogImportRowError,
    CatalogImportStatus,
    ProductAvailability,
    ProductImageRole,
    ReviewStatus,
    SearchIndexStatus,
)


@pytest.mark.asyncio
async def test_business_catalog_repository_round_trips_catalog_state() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlBusinessCatalogRepository(session_factory=session_factory)

    merchant = await repository.save_merchant(
        BusinessMerchant(
            merchant_id="merchant_1",
            owner_id="owner_1",
            display_name="Style Almaty",
            country_code="KZ",
            city="Almaty",
            status=BusinessMerchantStatus.ACTIVE,
        )
    )
    product = await repository.save_product(
        BusinessProduct(
            product_id="product_1",
            merchant_id=merchant.merchant_id,
            owner_id="owner_1",
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            status=BusinessProductStatus.SUBMITTED,
            review_status=ReviewStatus.PENDING,
            source_type="manual",
        )
    )
    offer = await repository.save_offer(
        BusinessProductOffer(
            offer_id="offer_1",
            product_id=product.product_id,
            price_amount=Decimal("14990"),
            currency="KZT",
            availability=ProductAvailability.IN_STOCK,
            delivery_regions=["Almaty", "Astana"],
        )
    )
    image = await repository.save_product_image(
        BusinessProductImage(
            image_id="image_1",
            product_id=product.product_id,
            object_key="catalog/product_1/source.png",
            content_type="image/png",
            size_bytes=2048,
            sha256="b" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        )
    )

    loaded_merchant = await repository.get_merchant_by_owner("owner_1")
    listed_merchants = await repository.list_merchants()
    loaded_product = await repository.get_product("product_1")
    loaded_offer = await repository.get_offer("product_1")
    loaded_images = await repository.list_product_images("product_1")
    owner_products = await repository.list_products("owner_1")

    assert loaded_merchant is not None
    assert loaded_merchant.merchant_id == merchant.merchant_id
    assert listed_merchants[0].merchant_id == merchant.merchant_id
    assert loaded_product is not None
    assert loaded_product.product_id == product.product_id
    assert loaded_offer is not None
    assert loaded_offer.offer_id == offer.offer_id
    assert loaded_images[0].image_id == image.image_id
    assert owner_products[0].product_id == product.product_id

    tiered_merchant = merchant.model_copy(
        update={
            "assigned_tier": "large",
            "tier_assigned_reason": "Large import volume.",
            "tier_assigned_by": "admin_1",
        }
    )
    await repository.save_merchant(tiered_merchant)
    loaded_tiered_merchant = await repository.get_merchant(merchant.merchant_id)
    load_metrics = await repository.get_catalog_load_metrics(tiered_merchant)

    assert loaded_tiered_merchant is not None
    assert loaded_tiered_merchant.assigned_tier == "large"
    assert loaded_tiered_merchant.tier_assigned_reason == "Large import volume."
    assert loaded_tiered_merchant.tier_assigned_by == "admin_1"
    assert load_metrics["product_count"] == 1
    assert load_metrics["images_last_30_days"] == 1

    reviewed = product.model_copy(
        update={
            "status": BusinessProductStatus.ACTIVE,
            "review_status": ReviewStatus.APPROVED,
            "search_index_status": SearchIndexStatus.PENDING,
        }
    )
    await repository.save_product(reviewed)
    loaded_reviewed = await repository.get_product("product_1")

    assert loaded_reviewed is not None
    assert loaded_reviewed.review_status is ReviewStatus.APPROVED
    assert loaded_reviewed.search_index_status is SearchIndexStatus.PENDING

    await repository.mark_search_indexed(product_ids=["product_1"])
    loaded_indexed = await repository.get_product("product_1")

    assert loaded_indexed is not None
    assert loaded_indexed.search_index_status is SearchIndexStatus.INDEXED
    assert loaded_indexed.search_index_error is None
    assert loaded_indexed.search_indexed_at is not None

    await repository.mark_search_index_failed(product_ids=["product_1"], reason="qdrant unavailable")
    loaded_failed = await repository.get_product("product_1")

    assert loaded_failed is not None
    assert loaded_failed.search_index_status is SearchIndexStatus.FAILED
    assert loaded_failed.search_index_error == "qdrant unavailable"

    await engine.dispose()


@pytest.mark.asyncio
async def test_business_catalog_repository_persists_import_job_and_errors() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlBusinessCatalogRepository(session_factory=session_factory)

    job = await repository.save_import_job(
        CatalogImportJob(
            import_id="import_1",
            merchant_id="merchant_1",
            owner_id="owner_1",
            filename="products.csv",
            status=CatalogImportStatus.COMPLETED_WITH_ERRORS,
            total_rows=2,
            accepted_rows=1,
            rejected_rows=1,
            error_summary="1 row rejected.",
        )
    )
    await repository.save_import_errors(
        [
            CatalogImportRowError(
                import_id=job.import_id,
                row_number=2,
                field_name="price_amount",
                safe_code="invalid_price",
                message="Price must be non-negative.",
            )
        ]
    )

    loaded_job = await repository.get_import_job("import_1")
    loaded_errors = await repository.list_import_errors("import_1")

    assert loaded_job is not None
    assert loaded_job.import_id == job.import_id
    assert len(loaded_errors) == 1
    assert loaded_errors[0].safe_code == "invalid_price"

    await engine.dispose()
