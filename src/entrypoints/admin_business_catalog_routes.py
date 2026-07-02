"""Admin-only business catalog review API routes."""

from __future__ import annotations

import hashlib
from typing import Annotated

from fastapi import APIRouter, Body, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.domain.business_catalog import BusinessMerchant, BusinessProduct
from src.domain.marketplace_search import MarketplaceDiscoveryCandidate, MarketplaceDiscoveryCandidateStatus, MarketplaceSourceType
from src.domain.similar_search import SimilarSearchClickAnalyticsResponse
from src.adapters.database.sql.similar_search_repositories import SqlMarketplaceCandidateRepository
from src.entrypoints.admin_auth import AdminActor, resolve_admin_actor
from src.entrypoints.business_catalog_routes import business_catalog_service
from src.entrypoints.runtime_dependencies import operations_runtime_dependencies, similar_search_runtime_dependencies
from src.settings import Settings
from src.use_cases.business_catalog.service import (
    BulkCategoryValidationResult,
    BulkProductApprovalResult,
    BusinessCatalogForbiddenError,
    BusinessCatalogNotFoundError,
    BusinessCatalogOperationError,
    BusinessCatalogValidationError,
)
from src.use_cases.business_catalog.tenant_partitioning import BusinessCatalogLoadMetrics, BusinessCatalogTenantTier
from src.use_cases.similar_search.candidate_review import (
    InMemoryMarketplaceCandidateRepository,
    MarketplaceCandidateReviewService,
)

router = APIRouter(prefix="/api/admin/business-catalog", tags=["admin-business-catalog"])


class AdminBusinessProductResponse(BaseModel):
    """Admin business product mutation response."""

    model_config = ConfigDict(extra="forbid")

    product: BusinessProduct


class AdminBusinessProductListResponse(BaseModel):
    """Admin pending business products response."""

    model_config = ConfigDict(extra="forbid")

    products: list[BusinessProduct]


class AdminMarketplaceDiscoveryCandidateResponse(BaseModel):
    """Admin marketplace discovery candidate mutation response."""

    model_config = ConfigDict(extra="forbid")

    candidate: MarketplaceDiscoveryCandidate


class AdminMarketplaceDiscoveryCandidateListResponse(BaseModel):
    """Admin marketplace discovery candidates response."""

    model_config = ConfigDict(extra="forbid")

    candidates: list[MarketplaceDiscoveryCandidate]


class AdminBusinessMerchantTierCard(BaseModel):
    """Admin workload tier card for one business merchant."""

    model_config = ConfigDict(extra="forbid")

    merchant: BusinessMerchant
    assigned_tier: BusinessCatalogTenantTier
    recommended_tier: BusinessCatalogTenantTier
    recommendation_reasons: list[str]
    metrics: BusinessCatalogLoadMetrics
    queue_partition: str
    storage_prefix: str
    rate_limit_bucket: str
    hot_account_mode: bool


class AdminBusinessMerchantTierListResponse(BaseModel):
    """Admin workload tier list response."""

    model_config = ConfigDict(extra="forbid")

    merchants: list[AdminBusinessMerchantTierCard]


class AdminBusinessMerchantTierResponse(BaseModel):
    """Admin workload tier mutation response."""

    model_config = ConfigDict(extra="forbid")

    merchant: AdminBusinessMerchantTierCard


class RejectBusinessProductPayload(BaseModel):
    """Admin reject request payload."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)


class RejectMarketplaceDiscoveryCandidatePayload(BaseModel):
    """Admin reject payload for a discovery candidate."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(default=None, min_length=1, max_length=512)


class ValidateBusinessProductCategoryPayload(BaseModel):
    """Admin category validation payload from a backend-owned visual analysis."""

    model_config = ConfigDict(extra="forbid")

    visual_category: str = Field(min_length=1, max_length=128)
    confidence: float = Field(ge=0.0, le=1.0)


class BulkValidateBusinessProductCategoryPayload(BaseModel):
    """Admin bulk category validation request payload."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=25)


class BulkValidateBusinessProductCategoryResponse(BaseModel):
    """Admin bulk category validation response."""

    model_config = ConfigDict(extra="forbid")

    result: BulkCategoryValidationResult


class BulkApproveBusinessProductPayload(BaseModel):
    """Admin bulk approve request payload."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=10, ge=1, le=25)


class BulkApproveBusinessProductResponse(BaseModel):
    """Admin bulk approve response."""

    model_config = ConfigDict(extra="forbid")

    result: BulkProductApprovalResult


class AssignBusinessMerchantTierPayload(BaseModel):
    """Admin merchant tier assignment request payload."""

    model_config = ConfigDict(extra="forbid")

    assigned_tier: BusinessCatalogTenantTier
    reason: str = Field(min_length=1)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""

    return request.app.state.settings


def _admin_actor(
    settings: Settings,
    authorization: str | None,
    admin_role: str | None,
    admin_id: str | None,
) -> AdminActor | JSONResponse:
    """Validate business catalog admin feature flag and role headers."""

    if not bool(getattr(settings, "enable_admin_business_catalog", False)):
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "business_catalog_admin_disabled",
                    "message": "Admin business catalog API is disabled.",
                }
            },
        )
    return resolve_admin_actor(
        settings=settings,
        allowed_roles={"admin", "catalog_admin"},
        authorization=authorization,
        legacy_admin_role=admin_role,
        legacy_admin_id=admin_id,
    )


def _service_or_error(settings: Settings):
    service = business_catalog_service(settings)
    if service is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "business_catalog_storage_unavailable",
                    "message": "Business catalog storage is not configured.",
                }
            },
        )
    return service


def marketplace_candidate_review_service(settings: Settings) -> MarketplaceCandidateReviewService:
    """Return candidate review service for admin-managed open-web candidates."""

    service = getattr(settings, "_marketplace_candidate_review_service", None)
    if service is None:
        sql_session_factory = getattr(settings, "sql_session_factory", None)
        repository = (
            SqlMarketplaceCandidateRepository(session_factory=sql_session_factory)
            if sql_session_factory is not None
            else InMemoryMarketplaceCandidateRepository()
        )
        service = MarketplaceCandidateReviewService(repository=repository)
        setattr(settings, "_marketplace_candidate_review_service", service)
    return service


def _error_response(exc: BusinessCatalogNotFoundError | BusinessCatalogForbiddenError | BusinessCatalogValidationError) -> JSONResponse:
    """Map business catalog admin errors to structured API errors."""

    if isinstance(exc, BusinessCatalogNotFoundError):
        return JSONResponse(status_code=404, content={"error": {"code": "business_catalog_not_found", "message": str(exc)}})
    if isinstance(exc, BusinessCatalogForbiddenError):
        return JSONResponse(status_code=403, content={"error": {"code": "business_catalog_forbidden", "message": str(exc)}})
    return JSONResponse(status_code=400, content={"error": {"code": "business_catalog_validation_failed", "message": str(exc)}})


def _operation_error_response(exc: BusinessCatalogOperationError) -> JSONResponse:
    """Map catalog operation failures to a structured retry-safe admin API error."""

    return JSONResponse(
        status_code=503,
        content={"error": {"code": exc.safe_code, "message": str(exc), "details": {}}},
    )


@router.get("/products/pending", response_model=AdminBusinessProductListResponse)
async def list_pending_business_products(
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessProductListResponse | JSONResponse:
    """List business products waiting for admin review."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    products = await service.list_pending_products_for_review()
    return AdminBusinessProductListResponse(products=products)


@router.get("/merchants/tiers", response_model=AdminBusinessMerchantTierListResponse)
async def list_business_merchant_tiers(
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessMerchantTierListResponse | JSONResponse:
    """List business merchants with workload tier recommendations."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    lister = getattr(service, "list_merchant_tier_cards", None)
    if lister is None:
        return AdminBusinessMerchantTierListResponse(merchants=[])
    return AdminBusinessMerchantTierListResponse(merchants=await lister())


@router.get("/analytics/similar-search", response_model=SimilarSearchClickAnalyticsResponse)
async def get_similar_search_click_analytics(
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
    limit: int = 10,
) -> SimilarSearchClickAnalyticsResponse | JSONResponse:
    """Return aggregate Similar Search click analytics for admin review."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    runtime = similar_search_runtime_dependencies(settings)
    return await runtime.click_event_service.get_analytics(limit=limit)


@router.get("/discovery-candidates/pending", response_model=AdminMarketplaceDiscoveryCandidateListResponse)
async def list_pending_marketplace_discovery_candidates(
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
    limit: int = 20,
) -> AdminMarketplaceDiscoveryCandidateListResponse | JSONResponse:
    """List marketplace/open-web discovery candidates waiting for admin review."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = marketplace_candidate_review_service(settings)
    return AdminMarketplaceDiscoveryCandidateListResponse(
        candidates=await service.list_pending_candidates(limit=limit),
    )


@router.get("/discovery-candidates", response_model=AdminMarketplaceDiscoveryCandidateListResponse)
async def list_marketplace_discovery_candidates(
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
    status: MarketplaceDiscoveryCandidateStatus | None = None,
    source_type: MarketplaceSourceType | None = None,
    category: str | None = None,
    city: str | None = None,
    workspace_id: str | None = None,
    business_id: str | None = None,
    limit: int = 20,
) -> AdminMarketplaceDiscoveryCandidateListResponse | JSONResponse:
    """List marketplace/open-web discovery candidates with admin filters."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = marketplace_candidate_review_service(settings)
    return AdminMarketplaceDiscoveryCandidateListResponse(
        candidates=await service.list_candidates(
            status=status,
            source_type=source_type,
            category=category,
            city=city,
            workspace_id=workspace_id,
            business_id=business_id,
            limit=limit,
        ),
    )


@router.post(
    "/discovery-candidates/{candidate_id}/approve",
    response_model=AdminMarketplaceDiscoveryCandidateResponse,
)
async def approve_marketplace_discovery_candidate(
    candidate_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminMarketplaceDiscoveryCandidateResponse | JSONResponse:
    """Approve one discovery candidate for downstream enrichment."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = marketplace_candidate_review_service(settings)
    candidate = await service.approve_candidate(candidate_id=candidate_id, admin_actor_id=actor.actor_id)
    return AdminMarketplaceDiscoveryCandidateResponse(candidate=candidate)


@router.post(
    "/discovery-candidates/{candidate_id}/reject",
    response_model=AdminMarketplaceDiscoveryCandidateResponse,
)
async def reject_marketplace_discovery_candidate(
    candidate_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    payload: Annotated[RejectMarketplaceDiscoveryCandidatePayload | None, Body()] = None,
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminMarketplaceDiscoveryCandidateResponse | JSONResponse:
    """Reject one discovery candidate so it cannot become a catalog source."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = marketplace_candidate_review_service(settings)
    candidate = await service.reject_candidate(
        candidate_id=candidate_id,
        admin_actor_id=actor.actor_id,
        rejection_reason=payload.reason if payload is not None else None,
    )
    return AdminMarketplaceDiscoveryCandidateResponse(candidate=candidate)


@router.post(
    "/discovery-candidates/{candidate_id}/archive",
    response_model=AdminMarketplaceDiscoveryCandidateResponse,
)
async def archive_marketplace_discovery_candidate(
    candidate_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminMarketplaceDiscoveryCandidateResponse | JSONResponse:
    """Archive one discovery candidate without approving it for enrichment."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = marketplace_candidate_review_service(settings)
    candidate = await service.archive_candidate(candidate_id=candidate_id, admin_actor_id=actor.actor_id)
    return AdminMarketplaceDiscoveryCandidateResponse(candidate=candidate)


@router.post("/merchants/{merchant_id}/tier", response_model=AdminBusinessMerchantTierResponse)
async def assign_business_merchant_tier(
    merchant_id: str,
    payload: AssignBusinessMerchantTierPayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessMerchantTierResponse | JSONResponse:
    """Assign one merchant workload tier after explicit admin approval."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    assigner = getattr(service, "assign_merchant_tier", None)
    if assigner is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "business_catalog_tier_storage_unavailable",
                    "message": "Business catalog tier storage is not configured.",
                }
            },
        )
    try:
        merchant = await assigner(
            admin_actor_id=actor.actor_id,
            merchant_id=merchant_id,
            assigned_tier=payload.assigned_tier,
            reason=payload.reason,
        )
    except BusinessCatalogOperationError as exc:
        return _operation_error_response(exc)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return AdminBusinessMerchantTierResponse(merchant=merchant)


@router.post("/products/{product_id}/approve", response_model=AdminBusinessProductResponse)
async def approve_business_product(
    product_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessProductResponse | JSONResponse:
    """Approve one submitted business product."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.approve_product(admin_actor_id=actor.actor_id, product_id=product_id)
        await _enqueue_search_index(settings=settings, product=product, source="admin_approve")
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return AdminBusinessProductResponse(product=product)


@router.post("/products/approve-matched-batch", response_model=BulkApproveBusinessProductResponse)
async def approve_matched_business_products(
    payload: BulkApproveBusinessProductPayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> BulkApproveBusinessProductResponse | JSONResponse:
    """Approve pending products that already passed backend category validation."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        result = await service.approve_matched_pending_products(admin_actor_id=actor.actor_id, limit=payload.limit)
        approved_ids = [item.product_id for item in result.items if item.status == "approved"]
        if approved_ids:
            await _enqueue_search_index_batch(settings=settings, product_ids=approved_ids, source="admin_approve_batch")
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return BulkApproveBusinessProductResponse(result=result)


@router.post("/products/{product_id}/category-validation", response_model=AdminBusinessProductResponse)
async def validate_business_product_category(
    product_id: str,
    payload: ValidateBusinessProductCategoryPayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessProductResponse | JSONResponse:
    """Persist visual category validation before admin product approval."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.record_product_category_validation(
            admin_actor_id=actor.actor_id,
            product_id=product_id,
            visual_category=payload.visual_category,
            confidence=payload.confidence,
        )
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return AdminBusinessProductResponse(product=product)


@router.post("/products/{product_id}/category-validation/run", response_model=AdminBusinessProductResponse)
async def run_business_product_category_validation(
    product_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessProductResponse | JSONResponse:
    """Run backend-owned visual category validation for one product primary image."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.run_product_category_validation(
            admin_actor_id=actor.actor_id,
            product_id=product_id,
        )
    except BusinessCatalogOperationError as exc:
        return _operation_error_response(exc)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return AdminBusinessProductResponse(product=product)


@router.post("/products/category-validation/run-batch", response_model=BulkValidateBusinessProductCategoryResponse)
async def run_pending_business_product_category_validations(
    payload: BulkValidateBusinessProductCategoryPayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> BulkValidateBusinessProductCategoryResponse | JSONResponse:
    """Run backend-owned category validation for pending products in a bounded batch."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        result = await service.run_pending_product_category_validations(
            admin_actor_id=actor.actor_id,
            limit=payload.limit,
        )
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return BulkValidateBusinessProductCategoryResponse(result=result)


@router.post("/products/{product_id}/reject", response_model=AdminBusinessProductResponse)
async def reject_business_product(
    product_id: str,
    payload: RejectBusinessProductPayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessProductResponse | JSONResponse:
    """Reject one submitted business product with an explicit reason."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.reject_product(admin_actor_id=actor.actor_id, product_id=product_id, reason=payload.reason)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return AdminBusinessProductResponse(product=product)


@router.post("/products/{product_id}/archive", response_model=AdminBusinessProductResponse)
async def archive_business_product(
    product_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessProductResponse | JSONResponse:
    """Archive one business product without deleting audit/history."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.archive_product_as_admin(admin_actor_id=actor.actor_id, product_id=product_id)
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return AdminBusinessProductResponse(product=product)


@router.post("/products/{product_id}/search-index/retry", response_model=AdminBusinessProductResponse)
async def retry_business_product_search_index(
    product_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> AdminBusinessProductResponse | JSONResponse:
    """Schedule one approved business product for search reindex."""

    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        product = await service.retry_product_search_index(admin_actor_id=actor.actor_id, product_id=product_id)
        await _enqueue_search_index(settings=settings, product=product, source="admin_retry")
    except (BusinessCatalogNotFoundError, BusinessCatalogForbiddenError, BusinessCatalogValidationError) as exc:
        return _error_response(exc)
    return AdminBusinessProductResponse(product=product)


async def _enqueue_search_index(*, settings: Settings, product: BusinessProduct, source: str) -> None:
    """Enqueue backend-owned search indexing for one approved catalog product."""

    operations_runtime = operations_runtime_dependencies(settings)
    await operations_runtime.dispatch_service.enqueue_workflow(
        workflow_type="business_catalog_search_index",
        workflow_reference=product.product_id,
        payload={"product_ids": [product.product_id], "source": source},
        idempotency_key=f"business_catalog_search_index:{product.product_id}:{product.updated_at.isoformat()}",
        max_attempts=3,
    )


async def _enqueue_search_index_batch(*, settings: Settings, product_ids: list[str], source: str) -> None:
    """Enqueue backend-owned search indexing for approved catalog products."""

    operations_runtime = operations_runtime_dependencies(settings)
    safe_ids = sorted(set(product_ids))
    batch_fingerprint = _search_index_batch_fingerprint(product_ids=safe_ids, source=source)
    await operations_runtime.dispatch_service.enqueue_workflow(
        workflow_type="business_catalog_search_index",
        workflow_reference=f"batch:{batch_fingerprint}",
        payload={"product_ids": safe_ids, "source": source},
        idempotency_key=f"business_catalog_search_index_batch:{batch_fingerprint}",
        max_attempts=3,
    )


def _search_index_batch_fingerprint(*, product_ids: list[str], source: str) -> str:
    """Build a short stable identifier for bounded batch indexing jobs."""

    raw = f"{source}:{','.join(product_ids)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
