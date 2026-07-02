from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.business_catalog import ProductAvailability, ProductImageRole
from src.use_cases.business_catalog.idempotency import InMemoryBusinessCatalogIdempotencyStore
from src.use_cases.business_catalog.service import (
    BusinessCatalogForbiddenError,
    BusinessCatalogService,
    BusinessCatalogValidationError,
    CreateProductRequest,
    ProductOfferInput,
    UploadProductImageRequest,
    UpsertMerchantRequest,
)
from tests.test_business_catalog_service import InMemoryBusinessCatalogRepository


class _BusinessCatalogFileStorage:
    def __init__(self) -> None:
        self.saved: list[dict[str, object]] = []

    async def save_upload(self, *, owner_id: str, filename: str, content_type: str, content: bytes) -> str:
        self.saved.append(
            {
                "owner_id": owner_id,
                "filename": filename,
                "content_type": content_type,
                "content": content,
            }
        )
        return f"business-catalog/{owner_id}/{filename}"


async def _seed_product(service: BusinessCatalogService) -> str:
    await service.upsert_merchant(
        "owner_1",
        UpsertMerchantRequest(display_name="Style Almaty", country_code="KZ", city="Almaty"),
    )
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


@pytest.mark.asyncio
async def test_business_catalog_service_uploads_primary_image_to_storage() -> None:
    storage = _BusinessCatalogFileStorage()
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository(), file_storage=storage)
    product_id = await _seed_product(service)

    image = await service.upload_product_image(
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

    assert image.role is ProductImageRole.PRIMARY
    assert image.object_key == f"business-catalog/owner_1/shirt.png"
    assert len(image.sha256) == 64
    assert storage.saved[0]["content"] == b"image-bytes"


@pytest.mark.asyncio
async def test_business_catalog_service_rejects_unsupported_image_type() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository(), file_storage=_BusinessCatalogFileStorage())
    product_id = await _seed_product(service)

    with pytest.raises(BusinessCatalogValidationError, match="Unsupported product image type"):
        await service.upload_product_image(
            "owner_1",
            UploadProductImageRequest(
                product_id=product_id,
                filename="shirt.gif",
                content_type="image/gif",
                content=b"image-bytes",
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )


@pytest.mark.asyncio
async def test_business_catalog_service_rejects_oversized_image() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository(), file_storage=_BusinessCatalogFileStorage())
    product_id = await _seed_product(service)

    with pytest.raises(BusinessCatalogValidationError, match="Product image exceeds"):
        await service.upload_product_image(
            "owner_1",
            UploadProductImageRequest(
                product_id=product_id,
                filename="shirt.png",
                content_type="image/png",
                content=b"x" * (10 * 1024 * 1024 + 1),
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )


@pytest.mark.asyncio
async def test_business_catalog_service_blocks_cross_owner_image_upload() -> None:
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository(), file_storage=_BusinessCatalogFileStorage())
    product_id = await _seed_product(service)

    with pytest.raises(BusinessCatalogForbiddenError):
        await service.upload_product_image(
            "owner_2",
            UploadProductImageRequest(
                product_id=product_id,
                filename="shirt.png",
                content_type="image/png",
                content=b"image-bytes",
                role=ProductImageRole.PRIMARY,
                sort_order=0,
            ),
        )


def test_business_catalog_upload_route_persists_primary_image(monkeypatch) -> None:
    from src.entrypoints.business_catalog_routes import router

    storage = _BusinessCatalogFileStorage()
    service = BusinessCatalogService(InMemoryBusinessCatalogRepository(), file_storage=storage)

    async def seed() -> str:
        return await _seed_product(service)

    import asyncio

    product_id = asyncio.run(seed())
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

    assert response.status_code == 200
    assert response.json()["image"]["role"] == "primary"
    assert storage.saved[0]["filename"] == "shirt.png"


def test_business_catalog_upload_route_uses_idempotency_key(monkeypatch) -> None:
    from src.entrypoints.business_catalog_routes import router

    storage = _BusinessCatalogFileStorage()
    repository = InMemoryBusinessCatalogRepository()
    service = BusinessCatalogService(
        repository,
        file_storage=storage,
        idempotency_store=InMemoryBusinessCatalogIdempotencyStore(),
    )

    async def seed() -> str:
        return await _seed_product(service)

    import asyncio

    product_id = asyncio.run(seed())
    app = FastAPI()
    app.state.settings = type("Settings", (), {"default_person_credit_account_id": "owner_1"})()
    app.include_router(router)
    monkeypatch.setattr(
        "src.entrypoints.business_catalog_routes.business_catalog_service",
        lambda settings: service,
    )
    client = TestClient(app)

    first = client.post(
        f"/api/business/products/{product_id}/images",
        headers={"Idempotency-Key": "image-key-1"},
        data={"role": "primary", "sort_order": "0"},
        files={"file": ("shirt.png", b"image-bytes", "image/png")},
    )
    second = client.post(
        f"/api/business/products/{product_id}/images",
        headers={"Idempotency-Key": "image-key-1"},
        data={"role": "primary", "sort_order": "0"},
        files={"file": ("shirt.png", b"image-bytes", "image/png")},
    )

    assert second.status_code == 200
    assert second.json()["image"]["image_id"] == first.json()["image"]["image_id"]
    assert len(storage.saved) == 1
    assert len(asyncio.run(repository.list_product_images(product_id))) == 1
