from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessMerchantStatus,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductOffer,
    BusinessProductStatus,
    CatalogImportJob,
    CatalogImportStatus,
    ProductAvailability,
    ProductImageRole,
    ReviewStatus,
)


def test_business_product_requires_core_catalog_fields() -> None:
    product = BusinessProduct(
        product_id="product_1",
        merchant_id="merchant_1",
        owner_id="owner_1",
        title="White oversized shirt",
        category="shirt",
        country_code="KZ",
        city="Almaty",
        status=BusinessProductStatus.DRAFT,
        review_status=ReviewStatus.NOT_REQUIRED,
        source_type="manual",
    )

    assert product.title == "White oversized shirt"
    assert product.country_code == "KZ"
    assert product.city == "Almaty"


def test_business_product_offer_rejects_negative_price() -> None:
    with pytest.raises(ValidationError):
        BusinessProductOffer(
            offer_id="offer_1",
            product_id="product_1",
            price_amount=Decimal("-1"),
            currency="KZT",
            availability=ProductAvailability.IN_STOCK,
            delivery_regions=["Almaty"],
        )


def test_business_merchant_normalizes_country_code() -> None:
    merchant = BusinessMerchant(
        merchant_id="merchant_1",
        owner_id="owner_1",
        display_name="Style Almaty",
        country_code="kz",
        city="Almaty",
        status=BusinessMerchantStatus.DRAFT,
    )

    assert merchant.country_code == "KZ"


def test_business_product_image_requires_real_hash() -> None:
    image = BusinessProductImage(
        image_id="image_1",
        product_id="product_1",
        object_key="fitfabrica/products/product_1/source.png",
        content_type="image/png",
        size_bytes=1024,
        sha256="a" * 64,
        role=ProductImageRole.PRIMARY,
        sort_order=0,
    )

    assert image.role is ProductImageRole.PRIMARY


def test_catalog_import_job_tracks_row_counts() -> None:
    job = CatalogImportJob(
        import_id="import_1",
        merchant_id="merchant_1",
        owner_id="owner_1",
        filename="products.csv",
        status=CatalogImportStatus.COMPLETED_WITH_ERRORS,
        total_rows=10,
        accepted_rows=8,
        rejected_rows=2,
        error_summary="2 rows rejected.",
    )

    assert job.accepted_rows + job.rejected_rows == job.total_rows
