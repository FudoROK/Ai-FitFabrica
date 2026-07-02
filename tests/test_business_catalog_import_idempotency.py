from __future__ import annotations

from decimal import Decimal

import pytest

from src.domain.business_catalog import ProductAvailability, ProductImageRole
from src.use_cases.business_catalog.idempotency import InMemoryBusinessCatalogIdempotencyStore
from src.use_cases.business_catalog.service import (
    AddProductImageRequest,
    BusinessCatalogService,
    BusinessCatalogValidationError,
    CreateProductRequest,
    ProductOfferInput,
    UpsertMerchantRequest,
    UploadProductImageRequest,
)
from tests.test_business_catalog_service import InMemoryBusinessCatalogRepository


class _CountingFileStorage:
    def __init__(self) -> None:
        self.save_calls = 0

    async def save_upload(self, *, owner_id: str, filename: str, content_type: str, content: bytes) -> str:
        self.save_calls += 1
        return f"business-catalog/{owner_id}/{filename}"


@pytest.mark.asyncio
async def test_csv_import_idempotency_key_prevents_duplicate_products() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository, idempotency_store=InMemoryBusinessCatalogIdempotencyStore())
    await _merchant(service)
    csv = (
        "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
        "White shirt,shirt,14990,KZT,KZ,Almaty,in_stock,https://example.com/shirt,Almaty\n"
    )

    first_job, first_errors = await service.import_products_from_csv(
        "owner_1",
        "products.csv",
        csv,
        idempotency_key="import-key-1",
    )
    second_job, second_errors = await service.import_products_from_csv(
        "owner_1",
        "products.csv",
        csv,
        idempotency_key="import-key-1",
    )

    assert second_job.import_id == first_job.import_id
    assert second_errors == first_errors
    assert len(await repository.list_products("owner_1")) == 1


@pytest.mark.asyncio
async def test_image_upload_idempotency_key_prevents_duplicate_storage_and_metadata() -> None:
    repository = InMemoryBusinessCatalogRepository()
    file_storage = _CountingFileStorage()
    service = BusinessCatalogService(
        repository,
        file_storage=file_storage,
        idempotency_store=InMemoryBusinessCatalogIdempotencyStore(),
    )
    product_id = await _product(service)
    request = UploadProductImageRequest(
        product_id=product_id,
        filename="shirt.png",
        content_type="image/png",
        content=b"image-bytes",
        role=ProductImageRole.PRIMARY,
        sort_order=0,
    )

    first = await service.upload_product_image("owner_1", request, idempotency_key="image-key-1")
    second = await service.upload_product_image("owner_1", request, idempotency_key="image-key-1")

    assert second.image_id == first.image_id
    assert file_storage.save_calls == 1
    assert len(await repository.list_product_images(product_id)) == 1


@pytest.mark.asyncio
async def test_submit_idempotency_key_prevents_duplicate_review_transition() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository, idempotency_store=InMemoryBusinessCatalogIdempotencyStore())
    product_id = await _product(service)
    await service.add_product_image(
        "owner_1",
        AddProductImageRequest(
            product_id=product_id,
            object_key="catalog/product_1/source.png",
            content_type="image/png",
            size_bytes=1024,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        ),
    )

    first = await service.submit_product("owner_1", product_id, idempotency_key="submit-key-1")
    save_count_after_first = repository.product_save_count
    second = await service.submit_product("owner_1", product_id, idempotency_key="submit-key-1")

    assert second.product_id == first.product_id
    assert repository.product_save_count == save_count_after_first


@pytest.mark.asyncio
async def test_failed_validation_is_not_cached_and_can_be_retried() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository, idempotency_store=InMemoryBusinessCatalogIdempotencyStore())
    product_id = await _product(service)

    with pytest.raises(BusinessCatalogValidationError):
        await service.submit_product("owner_1", product_id, idempotency_key="submit-key-1")

    await service.add_product_image(
        "owner_1",
        AddProductImageRequest(
            product_id=product_id,
            object_key="catalog/product_1/source.png",
            content_type="image/png",
            size_bytes=1024,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        ),
    )
    submitted = await service.submit_product("owner_1", product_id, idempotency_key="submit-key-1")

    assert submitted.product_id == product_id


async def _merchant(service: BusinessCatalogService) -> None:
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )


async def _product(service: BusinessCatalogService) -> str:
    await _merchant(service)
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
