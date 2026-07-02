from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.business_catalog import CatalogImportStatus, ProductAvailability, ProductImageRole
from src.use_cases.business_catalog.service import (
    BusinessCatalogOperationError,
    BusinessCatalogService,
    CreateProductRequest,
    ProductOfferInput,
    UploadProductImageRequest,
    UpsertMerchantRequest,
)
from tests.test_business_catalog_service import InMemoryBusinessCatalogRepository


class _FailingStorage:
    async def save_upload(self, *, owner_id: str, filename: str, content_type: str, content: bytes) -> str:
        raise RuntimeError("object storage unavailable")


class _MetadataFailingRepository(InMemoryBusinessCatalogRepository):
    async def save_product_image(self, image):
        raise RuntimeError("database unavailable after storage")


class _ImportErrorSaveFailingRepository(InMemoryBusinessCatalogRepository):
    async def save_import_errors(self, errors):
        raise RuntimeError("database unavailable while saving import errors")


class _RecordingStorage:
    def __init__(self) -> None:
        self.saved_keys: list[str] = []

    async def save_upload(self, *, owner_id: str, filename: str, content_type: str, content: bytes) -> str:
        object_key = f"business-catalog/{owner_id}/{filename}"
        self.saved_keys.append(object_key)
        return object_key


@pytest.mark.asyncio
async def test_storage_failure_returns_structured_operation_error_without_image_metadata() -> None:
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository, file_storage=_FailingStorage())
    product_id = await _seed_product(service)

    with pytest.raises(BusinessCatalogOperationError) as exc_info:
        await service.upload_product_image(
            "owner_1",
            UploadProductImageRequest(
                product_id=product_id,
                filename="shirt.png",
                content_type="image/png",
                content=b"image-bytes",
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )

    assert exc_info.value.safe_code == "business_catalog_storage_failed"
    assert await repository.list_product_images(product_id) == []


@pytest.mark.asyncio
async def test_metadata_failure_after_storage_records_cleanup_requirement() -> None:
    repository = _MetadataFailingRepository()
    storage = _RecordingStorage()
    service = BusinessCatalogService(repository, file_storage=storage)
    product_id = await _seed_product(service)

    with pytest.raises(BusinessCatalogOperationError) as exc_info:
        await service.upload_product_image(
            "owner_1",
            UploadProductImageRequest(
                product_id=product_id,
                filename="shirt.png",
                content_type="image/png",
                content=b"image-bytes",
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )

    assert exc_info.value.safe_code == "business_catalog_metadata_failed"
    assert exc_info.value.cleanup_required is True
    assert exc_info.value.cleanup_object_key == "business-catalog/owner_1/shirt.png"


@pytest.mark.asyncio
async def test_import_error_persistence_failure_marks_job_failed_with_reason() -> None:
    repository = _ImportErrorSaveFailingRepository()
    service = BusinessCatalogService(repository)
    await _merchant(service)
    csv_content = (
        "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
        "Bad price,shirt,-1,KZT,KZ,Almaty,in_stock,https://example.com/bad,Almaty\n"
    )

    job, errors = await service.import_products_from_csv("owner_1", "products.csv", csv_content)

    assert job.status is CatalogImportStatus.FAILED
    assert job.error_summary == "Failed to persist import row errors."
    assert errors[0].safe_code == "invalid_price"
    assert repository.import_jobs[job.import_id].status is CatalogImportStatus.FAILED


def test_upload_route_maps_operation_error_to_structured_response(monkeypatch) -> None:
    from src.entrypoints.business_catalog_routes import router

    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(repository, file_storage=_FailingStorage())

    import asyncio

    product_id = asyncio.run(_seed_product(service))
    app = FastAPI()
    app.state.settings = type("Settings", (), {"default_person_credit_account_id": "owner_1"})()
    app.include_router(router)
    monkeypatch.setattr(
        "src.entrypoints.business_catalog_routes.business_catalog_service",
        lambda settings: service,
    )
    client = TestClient(app)

    response = client.post(
        f"/api/business/products/{product_id}/images",
        data={"role": "primary", "sort_order": "0"},
        files={"file": ("shirt.png", b"image-bytes", "image/png")},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "business_catalog_storage_failed"
    assert response.json()["error"]["details"]["cleanup_required"] is False


async def _merchant(service: BusinessCatalogService) -> None:
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )


async def _seed_product(service: BusinessCatalogService) -> str:
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
