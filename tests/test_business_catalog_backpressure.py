from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.business_catalog import ProductAvailability, ProductImageRole
from src.use_cases.business_catalog.backpressure import BusinessCatalogBackpressurePolicy
from src.use_cases.business_catalog.service import (
    BusinessCatalogBackpressureError,
    BusinessCatalogService,
    CreateProductRequest,
    ProductOfferInput,
    UploadProductImageRequest,
    UpsertMerchantRequest,
)
from src.use_cases.business_catalog.tenant_partitioning import BusinessCatalogTenantTier
from tests.test_business_catalog_service import InMemoryBusinessCatalogRepository


class _Storage:
    async def save_upload(self, *, owner_id: str, filename: str, content_type: str, content: bytes) -> str:
        return f"business-catalog/{owner_id}/{filename}"


@pytest.mark.asyncio
async def test_standard_csv_import_rejects_more_than_1000_rows() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await _merchant(service, tier=BusinessCatalogTenantTier.STANDARD)
    csv_content = _csv_with_rows(1001)

    with pytest.raises(BusinessCatalogBackpressureError) as exc_info:
        await service.import_products_from_csv("owner_1", "products.csv", csv_content)

    assert exc_info.value.safe_code == "business_catalog_backpressure"
    assert exc_info.value.limit_name == "csv_rows"
    assert exc_info.value.limit_value == 1000
    assert exc_info.value.actual_value == 1001


@pytest.mark.asyncio
async def test_large_csv_import_allows_more_than_standard_limit() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())
    await _merchant(service, tier=BusinessCatalogTenantTier.LARGE)
    csv_content = _csv_with_rows(1001)

    job, errors = await service.import_products_from_csv("owner_1", "products.csv", csv_content)

    assert job.accepted_rows == 1001
    assert errors == []


@pytest.mark.asyncio
async def test_standard_csv_import_rejects_file_larger_than_5mb() -> None:
    policy = BusinessCatalogBackpressurePolicy(standard_csv_max_bytes=64)
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository(), backpressure_policy=policy)
    await _merchant(service, tier=BusinessCatalogTenantTier.STANDARD)

    with pytest.raises(BusinessCatalogBackpressureError) as exc_info:
        await service.import_products_from_csv("owner_1", "products.csv", _csv_with_rows(2))

    assert exc_info.value.limit_name == "csv_bytes"
    assert exc_info.value.limit_value == 64


@pytest.mark.asyncio
async def test_product_image_count_limit_blocks_extra_images() -> None:
    service = BusinessCatalogService(
        InMemoryBusinessCatalogRepository(),
        file_storage=_Storage(),
        backpressure_policy=BusinessCatalogBackpressurePolicy(standard_images_per_product=1),
    )
    product_id = await _product(service)
    await service.upload_product_image("owner_1", _image_request(product_id, "first.png"))

    with pytest.raises(BusinessCatalogBackpressureError) as exc_info:
        await service.upload_product_image("owner_1", _image_request(product_id, "second.png"))

    assert exc_info.value.limit_name == "images_per_product"
    assert exc_info.value.limit_value == 1
    assert exc_info.value.actual_value == 2


def test_import_route_maps_backpressure_to_structured_response(monkeypatch) -> None:
    from src.entrypoints.business_catalog_routes import router

    service = BusinessCatalogService(InMemoryBusinessCatalogRepository())

    import asyncio

    asyncio.run(_merchant(service, tier=BusinessCatalogTenantTier.STANDARD))
    app = FastAPI()
    app.state.settings = type("Settings", (), {"default_person_credit_account_id": "owner_1"})()
    app.include_router(router)
    monkeypatch.setattr("src.entrypoints.business_catalog_routes.business_catalog_service", lambda settings: service)
    client = TestClient(app)

    response = client.post(
        "/api/business/catalog-imports",
        files={"file": ("products.csv", _csv_with_rows(1001).encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "business_catalog_backpressure"
    assert response.json()["error"]["details"]["limit_name"] == "csv_rows"


async def _merchant(service: BusinessCatalogService, *, tier: BusinessCatalogTenantTier) -> None:
    merchant = await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
    await service.assign_merchant_tier(
        admin_actor_id="admin_1",
        merchant_id=merchant.merchant_id,
        assigned_tier=tier,
        reason="test setup",
    )


async def _product(service: BusinessCatalogService) -> str:
    await _merchant(service, tier=BusinessCatalogTenantTier.STANDARD)
    product = await service.create_product(
        "owner_1",
        CreateProductRequest(
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            offer=ProductOfferInput(
                price_amount=Decimal("14990"),
                currency="KZT",
                availability=ProductAvailability.IN_STOCK,
            ),
        ),
    )
    return product.product_id


def _image_request(product_id: str, filename: str) -> UploadProductImageRequest:
    return UploadProductImageRequest(
        product_id=product_id,
        filename=filename,
        content_type="image/png",
        content=b"image-bytes",
        role=ProductImageRole.PRIMARY,
        sort_order=0,
    )


def _csv_with_rows(row_count: int) -> str:
    header = "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
    rows = [
        f"Product {index},shirt,14990,KZT,KZ,Almaty,in_stock,https://example.com/{index},Almaty"
        for index in range(row_count)
    ]
    return header + "\n".join(rows)
