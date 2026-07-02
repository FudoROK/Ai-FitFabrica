from __future__ import annotations

from decimal import Decimal

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.business_catalog import (
    BusinessMerchant,
    BusinessMerchantStatus,
    BusinessProduct,
    BusinessProductImage,
    BusinessProductStatus,
    ProductAvailability,
    ProductImageRole,
    ReviewStatus,
)


class _BusinessCatalogService:
    def __init__(self) -> None:
        self.merchant = BusinessMerchant(
            merchant_id="merchant_1",
            owner_id="owner_1",
            display_name="Style Almaty",
            country_code="KZ",
            city="Almaty",
            status=BusinessMerchantStatus.ACTIVE,
        )
        self.products: list[BusinessProduct] = []
        self.primary_image = BusinessProductImage(
            image_id="image_1",
            product_id="product_approved",
            object_key="catalog/product_approved/primary.png",
            content_type="image/png",
            size_bytes=9,
            sha256="a" * 64,
            role=ProductImageRole.PRIMARY,
            sort_order=0,
        )

    async def get_merchant(self, owner_id: str):
        return self.merchant if owner_id == self.merchant.owner_id else None

    async def upsert_merchant(self, owner_id: str, request):
        self.merchant = BusinessMerchant(
            merchant_id="merchant_1",
            owner_id=owner_id,
            display_name=request.display_name,
            country_code=request.country_code,
            city=request.city,
            legal_name=request.legal_name,
            contact_email=request.contact_email,
            instagram_url=request.instagram_url,
            website_url=request.website_url,
            status=BusinessMerchantStatus.ACTIVE,
        )
        return self.merchant

    async def list_products(self, owner_id: str):
        return [product for product in self.products if product.owner_id == owner_id]

    async def create_product(self, owner_id: str, request):
        product = BusinessProduct(
            product_id="product_1",
            merchant_id=self.merchant.merchant_id,
            owner_id=owner_id,
            title=request.title,
            category=request.category,
            description=request.description,
            country_code=request.country_code,
            city=request.city,
            status=BusinessProductStatus.DRAFT,
            review_status=ReviewStatus.NOT_REQUIRED,
            source_type=request.source_type,
        )
        self.products.append(product)
        return product

    async def submit_product(self, owner_id: str, product_id: str, *, idempotency_key: str | None = None):
        self.last_idempotency_key = idempotency_key
        product = self.products[0]
        submitted = product.model_copy(
            update={
                "status": BusinessProductStatus.SUBMITTED,
                "review_status": ReviewStatus.PENDING,
            }
        )
        self.products[0] = submitted
        return submitted

    async def get_public_primary_product_image(self, product_id: str):
        if product_id != self.primary_image.product_id:
            return None
        return self.primary_image


def _client(monkeypatch, service: _BusinessCatalogService) -> TestClient:
    from src.entrypoints.business_catalog_routes import router

    app = FastAPI()
    app.state.settings = type("Settings", (), {"default_person_credit_account_id": "owner_1"})()
    app.include_router(router)
    monkeypatch.setattr(
        "src.entrypoints.business_catalog_routes.business_catalog_service",
        lambda settings: service,
    )
    monkeypatch.setattr(
        "src.entrypoints.business_catalog_routes.portable_infrastructure",
        lambda settings: type("Infrastructure", (), {"object_storage": type("Storage", (), {"get_bytes": lambda self, key: b"png-bytes"})()})(),
    )
    return TestClient(app)


def test_business_catalog_routes_read_and_save_merchant(monkeypatch) -> None:
    service = _BusinessCatalogService()
    client = _client(monkeypatch, service)

    get_response = client.get("/api/business/merchant")
    save_response = client.post(
        "/api/business/merchant",
        json={
            "display_name": "Updated Store",
            "country_code": "KZ",
            "city": "Astana",
        },
    )

    assert get_response.status_code == 200
    assert get_response.json()["merchant"]["display_name"] == "Style Almaty"
    assert save_response.status_code == 200
    assert save_response.json()["merchant"]["display_name"] == "Updated Store"


def test_business_catalog_routes_create_list_and_submit_product(monkeypatch) -> None:
    service = _BusinessCatalogService()
    client = _client(monkeypatch, service)

    create_response = client.post(
        "/api/business/products",
        json={
            "title": "White oversized shirt",
            "category": "shirt",
            "country_code": "KZ",
            "city": "Almaty",
            "offer": {
                "price_amount": str(Decimal("14990")),
                "currency": "KZT",
                "availability": ProductAvailability.IN_STOCK.value,
                "delivery_regions": ["Almaty"],
            },
        },
    )
    list_response = client.get("/api/business/products")
    submit_response = client.post("/api/business/products/product_1/submit")

    assert create_response.status_code == 200
    assert create_response.json()["product"]["status"] == "draft"
    assert list_response.status_code == 200
    assert list_response.json()["products"][0]["product_id"] == "product_1"
    assert submit_response.status_code == 200
    assert submit_response.json()["product"]["review_status"] == "pending"


def test_business_catalog_submit_route_forwards_idempotency_key(monkeypatch) -> None:
    service = _BusinessCatalogService()
    client = _client(monkeypatch, service)
    client.post(
        "/api/business/products",
        json={
            "title": "White oversized shirt",
            "category": "shirt",
            "country_code": "KZ",
            "city": "Almaty",
            "offer": {
                "price_amount": str(Decimal("14990")),
                "currency": "KZT",
                "availability": ProductAvailability.IN_STOCK.value,
                "delivery_regions": ["Almaty"],
            },
        },
    )

    response = client.post("/api/business/products/product_1/submit", headers={"Idempotency-Key": "submit-key-1"})

    assert response.status_code == 200
    assert service.last_idempotency_key == "submit-key-1"


def test_business_catalog_primary_image_route_returns_image_bytes(monkeypatch) -> None:
    service = _BusinessCatalogService()
    client = _client(monkeypatch, service)

    response = client.get("/api/business/products/product_approved/images/primary")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"png-bytes"
