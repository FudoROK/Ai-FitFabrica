from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.business_catalog import BusinessMerchant, BusinessMerchantStatus
from src.entrypoints.admin_business_catalog_routes import router
from src.use_cases.business_catalog.tenant_partitioning import (
    BusinessCatalogLoadMetrics,
    BusinessCatalogTenantTier,
    TenantPartitionPolicy,
)


class _Settings:
    enable_admin_business_catalog = True
    admin_api_token = "test-admin-token"
    allow_unsafe_admin_header_auth = False


class _AdminBusinessCatalogTierService:
    def __init__(self) -> None:
        self.merchant = BusinessMerchant(
            merchant_id="merchant_1",
            owner_id="owner_1",
            display_name="Style Almaty",
            country_code="KZ",
            city="Almaty",
            status=BusinessMerchantStatus.ACTIVE,
        )
        self.assigned_tier = BusinessCatalogTenantTier.STANDARD
        self.assigned_reason = "initial baseline"

    async def list_merchant_tier_cards(self):
        decision = TenantPartitionPolicy(shared_partition_count=8).resolve(
            owner_id=self.merchant.owner_id,
            merchant_id=self.merchant.merchant_id,
            assigned_tier=self.assigned_tier,
            metrics=BusinessCatalogLoadMetrics(
                product_count=20000,
                imports_last_30_days=12,
                largest_import_rows=25000,
                images_last_30_days=50000,
                failed_imports_last_30_days=1,
            ),
        )
        return [
            {
                "merchant": self.merchant,
                "assigned_tier": decision.assigned_tier,
                "recommended_tier": decision.recommended_tier,
                "recommendation_reasons": decision.recommendation_reasons,
                "metrics": {
                    "product_count": 20000,
                    "imports_last_30_days": 12,
                    "largest_import_rows": 25000,
                    "images_last_30_days": 50000,
                    "failed_imports_last_30_days": 1,
                },
                "queue_partition": decision.queue_partition,
                "storage_prefix": decision.storage_prefix,
                "rate_limit_bucket": decision.rate_limit_bucket,
                "hot_account_mode": decision.hot_account_mode,
            }
        ]

    async def assign_merchant_tier(self, *, admin_actor_id: str, merchant_id: str, assigned_tier, reason: str):
        assert admin_actor_id == "admin-api-token"
        assert merchant_id == "merchant_1"
        self.assigned_tier = assigned_tier
        self.assigned_reason = reason
        return (await self.list_merchant_tier_cards())[0]


def test_admin_lists_business_merchant_tier_recommendations(monkeypatch) -> None:
    service = _AdminBusinessCatalogTierService()
    client = _client(service=service, monkeypatch=monkeypatch)

    response = client.get("/api/admin/business-catalog/merchants/tiers", headers=_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["merchants"][0]["merchant"]["merchant_id"] == "merchant_1"
    assert payload["merchants"][0]["assigned_tier"] == "standard"
    assert payload["merchants"][0]["recommended_tier"] == "large"
    assert "large_catalog" in payload["merchants"][0]["recommendation_reasons"]
    assert payload["merchants"][0]["hot_account_mode"] is False


def test_admin_assigns_business_merchant_tier_manually(monkeypatch) -> None:
    service = _AdminBusinessCatalogTierService()
    client = _client(service=service, monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/business-catalog/merchants/merchant_1/tier",
        headers=_headers(),
        json={"assigned_tier": "large", "reason": "Client has large imports."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["merchant"]["assigned_tier"] == "large"
    assert payload["merchant"]["hot_account_mode"] is True
    assert service.assigned_reason == "Client has large imports."


def test_admin_tier_assignment_requires_reason(monkeypatch) -> None:
    client = _client(service=_AdminBusinessCatalogTierService(), monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/business-catalog/merchants/merchant_1/tier",
        headers=_headers(),
        json={"assigned_tier": "large", "reason": ""},
    )

    assert response.status_code == 422


def _client(*, service: _AdminBusinessCatalogTierService, monkeypatch) -> TestClient:
    app = FastAPI()
    app.state.settings = _Settings()
    app.include_router(router)
    monkeypatch.setattr("src.entrypoints.admin_business_catalog_routes.business_catalog_service", lambda settings: service)
    return TestClient(app)


def _headers() -> dict[str, str]:
    return {"authorization": "Bearer test-admin-token"}
