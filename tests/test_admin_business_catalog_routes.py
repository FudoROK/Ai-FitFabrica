from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.domain.business_catalog import (
    BusinessProduct,
    BusinessProductStatus,
    CategoryValidationStatus,
    ReviewStatus,
    SearchIndexStatus,
)
from src.domain.similar_search import (
    SimilarSearchClickAnalyticsItem,
    SimilarSearchClickAnalyticsResponse,
    SimilarSearchClickAnalyticsSummary,
)
from src.domain.marketplace_search import (
    MarketplaceConnectorKind,
    MarketplaceDiscoveryCandidate,
    MarketplaceDiscoveryCandidateStatus,
    MarketplaceSourceType,
)
from src.use_cases.business_catalog.service import BulkProductApprovalItem, BulkProductApprovalResult


class _AdminBusinessCatalogService:
    def __init__(self) -> None:
        self.product = BusinessProduct(
            product_id="product_1",
            merchant_id="merchant_1",
            owner_id="owner_1",
            title="White oversized shirt",
            category="shirt",
            country_code="KZ",
            city="Almaty",
            status=BusinessProductStatus.SUBMITTED,
            review_status=ReviewStatus.PENDING,
            source_type="manual",
        )
        self.approved: list[tuple[str, str]] = []
        self.rejected: list[tuple[str, str, str]] = []
        self.archived: list[tuple[str, str]] = []
        self.category_validations: list[tuple[str, str, str, float]] = []
        self.search_index_retries: list[tuple[str, str]] = []

    async def list_pending_products_for_review(self):
        return [self.product]

    async def approve_product(self, admin_actor_id: str, product_id: str):
        self.approved.append((admin_actor_id, product_id))
        self.product = self.product.model_copy(
            update={
                "status": BusinessProductStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
            }
        )
        return self.product

    async def reject_product(self, admin_actor_id: str, product_id: str, reason: str):
        self.rejected.append((admin_actor_id, product_id, reason))
        self.product = self.product.model_copy(
            update={
                "status": BusinessProductStatus.REJECTED,
                "review_status": ReviewStatus.REJECTED,
                "review_reason": reason,
            }
        )
        return self.product

    async def record_product_category_validation(
        self,
        admin_actor_id: str,
        product_id: str,
        *,
        visual_category: str,
        confidence: float,
    ):
        self.category_validations.append((admin_actor_id, product_id, visual_category, confidence))
        self.product = self.product.model_copy(
            update={
                "category_validation_status": CategoryValidationStatus.MATCHED,
                "category_validation_reason": "declared category 'shirt' matches visual category 'shirt'",
                "visual_category": visual_category,
                "visual_category_confidence": confidence,
            }
        )
        return self.product

    async def run_product_category_validation(self, admin_actor_id: str, product_id: str):
        self.category_validations.append((admin_actor_id, product_id, "shirt", 0.95))
        self.product = self.product.model_copy(
            update={
                "category_validation_status": CategoryValidationStatus.MATCHED,
                "category_validation_reason": "declared category 'shirt' matches visual category 'shirt'",
                "visual_category": "shirt",
                "visual_category_confidence": 0.95,
            }
        )
        return self.product

    async def run_pending_product_category_validations(self, admin_actor_id: str, *, limit: int = 10):
        self.category_validations.append((admin_actor_id, "batch", "limit", float(limit)))
        return {
            "requested_limit": limit,
            "processed_count": 1,
            "validated_count": 1,
            "failed_count": 0,
            "items": [
                {
                    "product_id": self.product.product_id,
                    "status": "validated",
                    "product": self.product.model_copy(update={"category_validation_status": CategoryValidationStatus.MATCHED}),
                    "error_message": None,
                }
            ],
        }

    async def approve_matched_pending_products(self, admin_actor_id: str, *, limit: int = 10):
        self.approved.append((admin_actor_id, f"batch:{limit}"))
        approved_product = self.product.model_copy(
            update={
                "status": BusinessProductStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "search_index_status": SearchIndexStatus.PENDING,
            }
        )
        return BulkProductApprovalResult(
            requested_limit=limit,
            processed_count=1,
            approved_count=1,
            failed_count=0,
            items=[
                BulkProductApprovalItem(
                    product_id=approved_product.product_id,
                    status="approved",
                    product=approved_product,
                    error_message=None,
                )
            ],
        )

    async def archive_product_as_admin(self, admin_actor_id: str, product_id: str):
        self.archived.append((admin_actor_id, product_id))
        self.product = self.product.model_copy(update={"status": BusinessProductStatus.ARCHIVED})
        return self.product

    async def retry_product_search_index(self, admin_actor_id: str, product_id: str):
        self.search_index_retries.append((admin_actor_id, product_id))
        self.product = self.product.model_copy(
            update={
                "status": BusinessProductStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "search_index_status": SearchIndexStatus.PENDING,
                "search_index_error": None,
            }
        )
        return self.product


class _DispatchService:
    def __init__(self) -> None:
        self.jobs: list[dict[str, object]] = []

    async def enqueue_workflow(self, **kwargs):
        self.jobs.append(kwargs)
        return object()


class _OperationsRuntime:
    def __init__(self) -> None:
        self.dispatch_service = _DispatchService()


class _ClickEventService:
    async def get_analytics(self, *, limit: int = 10):
        return SimilarSearchClickAnalyticsResponse(
            summary=SimilarSearchClickAnalyticsSummary(total_clicks=4, redirect_clicks=3, local_only_clicks=1),
            top_products=[
                SimilarSearchClickAnalyticsItem(key="product_1", label="White shirt", click_count=3),
            ],
            top_marketplaces=[
                SimilarSearchClickAnalyticsItem(key="local_catalog", label="local_catalog", click_count=4),
            ],
            top_cities=[
                SimilarSearchClickAnalyticsItem(key="Almaty", label="Almaty", click_count=4),
            ],
        )


class _SimilarSearchRuntime:
    def __init__(self) -> None:
        self.click_event_service = _ClickEventService()


class _CandidateReviewService:
    def __init__(self) -> None:
        self.candidate = MarketplaceDiscoveryCandidate(
            candidate_id="candidate_1",
            connector_kind=MarketplaceConnectorKind.INSTAGRAM_PUBLIC_DISCOVERY,
            source_type=MarketplaceSourceType.SEARCH_ENGINE_DISCOVERY,
            source_url="https://www.instagram.com/example_shop/p/example",
            source_title="Example shop white shirt",
            platform_hint="instagram",
            category="shirt",
            country_code="KZ",
            city="Almaty",
        )
        self.approved: list[tuple[str, str]] = []
        self.rejected: list[tuple[str, str]] = []

    async def list_pending_candidates(self, *, limit: int = 20):
        return (
            [self.candidate]
            if self.candidate.status
            in {MarketplaceDiscoveryCandidateStatus.PENDING, MarketplaceDiscoveryCandidateStatus.NEEDS_REVIEW}
            else []
        )

    async def approve_candidate(self, *, candidate_id: str, admin_actor_id: str):
        self.approved.append((admin_actor_id, candidate_id))
        self.candidate = self.candidate.model_copy(update={"status": MarketplaceDiscoveryCandidateStatus.APPROVED})
        return self.candidate

    async def reject_candidate(self, *, candidate_id: str, admin_actor_id: str, rejection_reason: str | None = None):
        self.rejected.append((admin_actor_id, candidate_id))
        self.candidate = self.candidate.model_copy(update={"status": MarketplaceDiscoveryCandidateStatus.REJECTED})
        return self.candidate

    async def archive_candidate(self, *, candidate_id: str, admin_actor_id: str):
        self.candidate = self.candidate.model_copy(update={"status": MarketplaceDiscoveryCandidateStatus.ARCHIVED})
        return self.candidate

    async def list_candidates(self, **kwargs):
        return [self.candidate]


def _client(
    *,
    enabled: bool,
    monkeypatch,
    service: _AdminBusinessCatalogService | None = None,
    operations_runtime: _OperationsRuntime | None = None,
    candidate_review_service: _CandidateReviewService | None = None,
    admin_api_token: str | None = "test-admin-token",
    allow_unsafe_admin_header_auth: bool = False,
) -> TestClient:
    from src.entrypoints.admin_business_catalog_routes import router

    app = FastAPI()
    app.state.settings = type(
        "Settings",
        (),
        {
            "enable_admin_business_catalog": enabled,
            "admin_api_token": admin_api_token,
            "allow_unsafe_admin_header_auth": allow_unsafe_admin_header_auth,
        },
    )()
    app.include_router(router)
    monkeypatch.setattr(
        "src.entrypoints.admin_business_catalog_routes.business_catalog_service",
        lambda settings: service,
    )
    monkeypatch.setattr(
        "src.entrypoints.admin_business_catalog_routes.operations_runtime_dependencies",
        lambda settings: operations_runtime or _OperationsRuntime(),
        raising=False,
    )
    monkeypatch.setattr(
        "src.entrypoints.admin_business_catalog_routes.similar_search_runtime_dependencies",
        lambda settings: _SimilarSearchRuntime(),
        raising=False,
    )
    monkeypatch.setattr(
        "src.entrypoints.admin_business_catalog_routes.marketplace_candidate_review_service",
        lambda settings: candidate_review_service or _CandidateReviewService(),
        raising=False,
    )
    return TestClient(app)


def _headers() -> dict[str, str]:
    return {"authorization": "Bearer test-admin-token"}


def _legacy_headers() -> dict[str, str]:
    return {
        "x-fitfabrica-admin-role": "catalog_admin",
        "x-fitfabrica-admin-id": "admin-1",
    }


def test_admin_business_catalog_routes_are_disabled_by_default(monkeypatch) -> None:
    client = _client(enabled=False, service=_AdminBusinessCatalogService(), monkeypatch=monkeypatch)

    response = client.post("/api/admin/business-catalog/products/product_1/approve", headers=_headers())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "business_catalog_admin_disabled"


def test_admin_business_catalog_routes_require_admin_header(monkeypatch) -> None:
    client = _client(enabled=True, service=_AdminBusinessCatalogService(), monkeypatch=monkeypatch)

    response = client.post("/api/admin/business-catalog/products/product_1/approve")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_auth_invalid"


def test_admin_business_catalog_rejects_legacy_headers_without_explicit_unsafe_mode(monkeypatch) -> None:
    client = _client(enabled=True, service=_AdminBusinessCatalogService(), monkeypatch=monkeypatch)

    response = client.get("/api/admin/business-catalog/products/pending", headers=_legacy_headers())

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_auth_invalid"


def test_admin_business_catalog_allows_legacy_headers_only_in_explicit_unsafe_mode(monkeypatch) -> None:
    client = _client(
        enabled=True,
        service=_AdminBusinessCatalogService(),
        monkeypatch=monkeypatch,
        admin_api_token=None,
        allow_unsafe_admin_header_auth=True,
    )

    response = client.get("/api/admin/business-catalog/products/pending", headers=_legacy_headers())

    assert response.status_code == 200


def test_admin_business_catalog_lists_pending_products(monkeypatch) -> None:
    client = _client(enabled=True, service=_AdminBusinessCatalogService(), monkeypatch=monkeypatch)

    response = client.get("/api/admin/business-catalog/products/pending", headers=_headers())

    assert response.status_code == 200
    assert response.json()["products"][0]["product_id"] == "product_1"
    assert response.json()["products"][0]["review_status"] == "pending"


def test_admin_business_catalog_returns_similar_search_click_analytics(monkeypatch) -> None:
    client = _client(enabled=True, service=_AdminBusinessCatalogService(), monkeypatch=monkeypatch)

    response = client.get("/api/admin/business-catalog/analytics/similar-search", headers=_headers())

    assert response.status_code == 200
    assert response.json()["summary"]["total_clicks"] == 4
    assert response.json()["summary"]["redirect_clicks"] == 3
    assert response.json()["top_products"][0]["key"] == "product_1"
    assert response.json()["top_cities"][0]["label"] == "Almaty"


def test_admin_business_catalog_reviews_marketplace_discovery_candidates(monkeypatch) -> None:
    candidate_service = _CandidateReviewService()
    client = _client(
        enabled=True,
        service=_AdminBusinessCatalogService(),
        candidate_review_service=candidate_service,
        monkeypatch=monkeypatch,
    )

    pending = client.get("/api/admin/business-catalog/discovery-candidates/pending", headers=_headers())
    approved = client.post("/api/admin/business-catalog/discovery-candidates/candidate_1/approve", headers=_headers())
    rejected = client.post("/api/admin/business-catalog/discovery-candidates/candidate_1/reject", headers=_headers())

    assert pending.status_code == 200
    assert pending.json()["candidates"][0]["candidate_id"] == "candidate_1"
    assert approved.status_code == 200
    assert approved.json()["candidate"]["status"] == "approved"
    assert rejected.status_code == 200
    assert rejected.json()["candidate"]["status"] == "rejected"
    assert candidate_service.approved == [("admin-api-token", "candidate_1")]
    assert candidate_service.rejected == [("admin-api-token", "candidate_1")]


def test_marketplace_candidate_review_service_uses_sql_repository_when_available() -> None:
    from src.adapters.database.sql.similar_search_repositories import SqlMarketplaceCandidateRepository
    from src.entrypoints.admin_business_catalog_routes import marketplace_candidate_review_service

    settings = type(
        "Settings",
        (),
        {
            "sql_session_factory": object(),
        },
    )()

    service = marketplace_candidate_review_service(settings)

    assert isinstance(service._repository, SqlMarketplaceCandidateRepository)


def test_admin_business_catalog_approve_and_reject(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    client = _client(enabled=True, service=service, monkeypatch=monkeypatch)

    approve = client.post("/api/admin/business-catalog/products/product_1/approve", headers=_headers())
    reject = client.post(
        "/api/admin/business-catalog/products/product_1/reject",
        headers=_headers(),
        json={"reason": "Image quality is not acceptable."},
    )

    assert approve.status_code == 200
    assert approve.json()["product"]["review_status"] == "approved"
    assert reject.status_code == 200
    assert reject.json()["product"]["review_status"] == "rejected"
    assert service.approved == [("admin-api-token", "product_1")]
    assert service.rejected == [("admin-api-token", "product_1", "Image quality is not acceptable.")]


def test_admin_business_catalog_archives_product(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    client = _client(enabled=True, service=service, monkeypatch=monkeypatch)

    response = client.post("/api/admin/business-catalog/products/product_1/archive", headers=_headers())

    assert response.status_code == 200
    assert response.json()["product"]["status"] == "archived"
    assert service.archived == [("admin-api-token", "product_1")]


def test_admin_business_catalog_records_category_validation(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    client = _client(enabled=True, service=service, monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/business-catalog/products/product_1/category-validation",
        headers=_headers(),
        json={"visual_category": "shirt", "confidence": 0.94},
    )

    assert response.status_code == 200
    assert response.json()["product"]["category_validation_status"] == "matched"
    assert response.json()["product"]["visual_category"] == "shirt"
    assert response.json()["product"]["visual_category_confidence"] == 0.94
    assert service.category_validations == [("admin-api-token", "product_1", "shirt", 0.94)]


def test_admin_business_catalog_runs_category_validation(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    client = _client(enabled=True, service=service, monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/business-catalog/products/product_1/category-validation/run",
        headers=_headers(),
    )

    assert response.status_code == 200
    assert response.json()["product"]["category_validation_status"] == "matched"
    assert response.json()["product"]["visual_category"] == "shirt"
    assert response.json()["product"]["visual_category_confidence"] == 0.95
    assert service.category_validations == [("admin-api-token", "product_1", "shirt", 0.95)]


def test_admin_business_catalog_runs_category_validation_batch(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    client = _client(enabled=True, service=service, monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/business-catalog/products/category-validation/run-batch",
        headers=_headers(),
        json={"limit": 5},
    )

    assert response.status_code == 200
    assert response.json()["result"]["requested_limit"] == 5
    assert response.json()["result"]["processed_count"] == 1
    assert response.json()["result"]["validated_count"] == 1
    assert service.category_validations == [("admin-api-token", "batch", "limit", 5.0)]


def test_admin_business_catalog_approves_matched_batch(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    operations_runtime = _OperationsRuntime()
    client = _client(enabled=True, service=service, operations_runtime=operations_runtime, monkeypatch=monkeypatch)

    response = client.post(
        "/api/admin/business-catalog/products/approve-matched-batch",
        headers=_headers(),
        json={"limit": 5},
    )

    assert response.status_code == 200
    assert response.json()["result"]["requested_limit"] == 5
    assert response.json()["result"]["approved_count"] == 1
    assert service.approved == [("admin-api-token", "batch:5")]
    assert operations_runtime.dispatch_service.jobs[0]["workflow_type"] == "business_catalog_search_index"
    assert operations_runtime.dispatch_service.jobs[0]["payload"]["product_ids"] == ["product_1"]


@pytest.mark.asyncio
async def test_admin_business_catalog_batch_index_job_uses_short_reference(monkeypatch) -> None:
    from src.entrypoints import admin_business_catalog_routes as routes

    operations_runtime = _OperationsRuntime()
    monkeypatch.setattr(
        routes,
        "operations_runtime_dependencies",
        lambda settings: operations_runtime,
    )
    product_ids = [f"product_{index:02d}_{'x' * 32}" for index in range(25)]

    await routes._enqueue_search_index_batch(settings=object(), product_ids=product_ids, source="admin_approve_batch")

    job = operations_runtime.dispatch_service.jobs[0]
    assert job["workflow_reference"].startswith("batch:")
    assert len(job["workflow_reference"]) <= 64
    assert len(job["idempotency_key"]) <= 64
    assert job["payload"]["product_ids"] == sorted(product_ids)


def test_admin_business_catalog_approve_enqueues_search_index_job(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    operations_runtime = _OperationsRuntime()
    client = _client(enabled=True, service=service, operations_runtime=operations_runtime, monkeypatch=monkeypatch)

    response = client.post("/api/admin/business-catalog/products/product_1/approve", headers=_headers())

    assert response.status_code == 200
    assert operations_runtime.dispatch_service.jobs[0]["workflow_type"] == "business_catalog_search_index"
    assert operations_runtime.dispatch_service.jobs[0]["workflow_reference"] == "product_1"
    assert operations_runtime.dispatch_service.jobs[0]["payload"]["product_ids"] == ["product_1"]


def test_admin_business_catalog_retries_search_index(monkeypatch) -> None:
    service = _AdminBusinessCatalogService()
    operations_runtime = _OperationsRuntime()
    client = _client(enabled=True, service=service, operations_runtime=operations_runtime, monkeypatch=monkeypatch)

    response = client.post("/api/admin/business-catalog/products/product_1/search-index/retry", headers=_headers())

    assert response.status_code == 200
    assert response.json()["product"]["search_index_status"] == "pending"
    assert service.search_index_retries == [("admin-api-token", "product_1")]
    assert operations_runtime.dispatch_service.jobs[0]["workflow_type"] == "business_catalog_search_index"
    assert operations_runtime.dispatch_service.jobs[0]["payload"]["source"] == "admin_retry"


def test_admin_business_catalog_reports_storage_unavailable(monkeypatch) -> None:
    client = _client(enabled=True, service=None, monkeypatch=monkeypatch)

    response = client.post("/api/admin/business-catalog/products/product_1/approve", headers=_headers())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "business_catalog_storage_unavailable"
