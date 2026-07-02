from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.business_catalog import CatalogImportJob, CatalogImportRowError
from src.use_cases.business_catalog.service import BusinessCatalogService
from tests.test_business_catalog_service import InMemoryBusinessCatalogRepository


class _ImportBusinessCatalogService(BusinessCatalogService):
    def __init__(self) -> None:
        super().__init__(InMemoryBusinessCatalogRepository())
        self.last_job: CatalogImportJob | None = None
        self.last_errors: list[CatalogImportRowError] = []
        self.last_idempotency_key: str | None = None

    async def import_products_from_csv(self, owner_id: str, filename: str, content: str, *, idempotency_key: str | None = None):
        self.last_idempotency_key = idempotency_key
        job, errors = await super().import_products_from_csv(owner_id, filename, content, idempotency_key=idempotency_key)
        self.last_job = job
        self.last_errors = errors
        return job, errors

    async def get_import_job(self, owner_id: str, import_id: str):
        if self.last_job is None or self.last_job.import_id != import_id or self.last_job.owner_id != owner_id:
            return None
        return self.last_job

    async def list_import_errors(self, owner_id: str, import_id: str):
        if self.last_job is None or self.last_job.import_id != import_id or self.last_job.owner_id != owner_id:
            return []
        return list(self.last_errors)


def _client(monkeypatch, service: _ImportBusinessCatalogService) -> TestClient:
    from src.entrypoints.business_catalog_routes import router

    app = FastAPI()
    app.state.settings = type("Settings", (), {"default_person_credit_account_id": "owner_1"})()
    app.include_router(router)
    monkeypatch.setattr(
        "src.entrypoints.business_catalog_routes.business_catalog_service",
        lambda settings: service,
    )
    return TestClient(app)


def test_business_catalog_import_route_accepts_partial_csv(monkeypatch) -> None:
    service = _ImportBusinessCatalogService()
    client = _client(monkeypatch, service)
    client.post("/api/business/merchant", json={"display_name": "Style Almaty", "country_code": "KZ", "city": "Almaty"})
    csv_content = (
        "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
        "White shirt,shirt,14990,KZT,KZ,Almaty,in_stock,https://example.com/shirt,Almaty\n"
        "Bad price,shirt,-1,KZT,KZ,Almaty,in_stock,https://example.com/bad,Almaty\n"
    )

    response = client.post(
        "/api/business/catalog-imports",
        files={"file": ("products.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["import_job"]["status"] == "completed_with_errors"
    assert response.json()["import_job"]["accepted_rows"] == 1
    assert response.json()["import_job"]["rejected_rows"] == 1
    assert response.json()["errors"][0]["safe_code"] == "invalid_price"


def test_business_catalog_import_route_forwards_idempotency_key(monkeypatch) -> None:
    service = _ImportBusinessCatalogService()
    client = _client(monkeypatch, service)
    client.post("/api/business/merchant", json={"display_name": "Style Almaty", "country_code": "KZ", "city": "Almaty"})
    csv_content = (
        "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
        "White shirt,shirt,14990,KZT,KZ,Almaty,in_stock,https://example.com/shirt,Almaty\n"
    )

    response = client.post(
        "/api/business/catalog-imports",
        headers={"Idempotency-Key": "import-key-1"},
        files={"file": ("products.csv", csv_content.encode("utf-8"), "text/csv")},
    )

    assert response.status_code == 200
    assert service.last_idempotency_key == "import-key-1"


def test_business_catalog_import_routes_return_job_and_errors(monkeypatch) -> None:
    service = _ImportBusinessCatalogService()
    client = _client(monkeypatch, service)
    client.post("/api/business/merchant", json={"display_name": "Style Almaty", "country_code": "KZ", "city": "Almaty"})
    csv_content = (
        "title,category,price_amount,currency,country_code,city,availability,product_url,delivery_regions\n"
        "Bad price,shirt,-1,KZT,KZ,Almaty,in_stock,https://example.com/bad,Almaty\n"
    )
    create = client.post(
        "/api/business/catalog-imports",
        files={"file": ("products.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    import_id = create.json()["import_job"]["import_id"]

    job_response = client.get(f"/api/business/catalog-imports/{import_id}")
    errors_response = client.get(f"/api/business/catalog-imports/{import_id}/errors")

    assert job_response.status_code == 200
    assert job_response.json()["import_job"]["import_id"] == import_id
    assert errors_response.status_code == 200
    assert errors_response.json()["errors"][0]["safe_code"] == "invalid_price"
