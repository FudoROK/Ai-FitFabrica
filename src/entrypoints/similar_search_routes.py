"""FastAPI routes for backend-owned similar search."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse

from src.domain.similar_search import (
    SimilarSearchClickEventRequest,
    SimilarSearchClickEventResponse,
    SimilarSearchGarmentProfile,
    SimilarSearchRequest,
    SimilarSearchResponse,
)
from src.entrypoints.runtime_dependencies import similar_search_runtime_dependencies
from src.settings import Settings
from src.use_cases.product_card.garment_identity_errors import GarmentIdentityAnalysisFailure
from src.use_cases.similar_search.events import SimilarSearchClickEventRejected

router = APIRouter()

_ALLOWED_GARMENT_PHOTO_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
_MAX_GARMENT_PHOTO_BYTES = 10 * 1024 * 1024


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


@router.post("/api/similar-search", response_model=SimilarSearchResponse)
async def create_similar_search(
    request: SimilarSearchRequest,
    settings: Annotated[Settings, Depends(_settings)],
) -> SimilarSearchResponse:
    """Execute backend-owned similar search and return structured results."""
    runtime = similar_search_runtime_dependencies(settings)
    return await runtime.workflow_service.search(request)


@router.post("/api/similar-search/garment-photo", response_model=SimilarSearchResponse)
async def create_similar_search_from_garment_photo(
    settings: Annotated[Settings, Depends(_settings)],
    garment_photo: Annotated[UploadFile, File()],
    budget_max: Annotated[str | None, Form()] = None,
    user_country_code: Annotated[str | None, Form()] = None,
    user_city: Annotated[str | None, Form()] = None,
    limit: Annotated[int, Form(gt=0, le=50)] = 10,
) -> SimilarSearchResponse | JSONResponse:
    """Analyze an uploaded garment photo and run backend-owned local-first similar search."""

    content_type = garment_photo.content_type or ""
    extension = _ALLOWED_GARMENT_PHOTO_TYPES.get(content_type)
    if extension is None:
        return _validation_error("similar_search_garment_photo_type_unsupported", "Upload JPEG, PNG, or WebP garment photo.")
    payload = await garment_photo.read()
    if not payload:
        return _validation_error("similar_search_garment_photo_empty", "Garment photo is required.")
    if len(payload) > _MAX_GARMENT_PHOTO_BYTES:
        return _validation_error("similar_search_garment_photo_too_large", "Garment photo must be 10 MB or smaller.")

    parsed_budget = _parse_optional_decimal(budget_max)
    if parsed_budget == "invalid":
        return _validation_error("similar_search_budget_invalid", "Budget must be a positive number.")

    runtime = similar_search_runtime_dependencies(settings)
    job_id = f"similar_{uuid4().hex}"
    object_key = f"{runtime.object_storage_root_prefix}/similar-search/{job_id}/garment{extension}"
    runtime.object_storage.put_bytes(object_key=object_key, payload=payload, content_type=content_type)
    try:
        analysis = await runtime.garment_identity_analyzer.analyze(job_id=job_id, asset_keys=[object_key])
    except GarmentIdentityAnalysisFailure as exc:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": exc.safe_code,
                    "message": "Garment photo analysis is temporarily unavailable. Please try again later.",
                    "details": {"job_id": job_id},
                }
            },
        )
    request = SimilarSearchRequest(
        source_type="garment_photo",
        garment_profile=SimilarSearchGarmentProfile(
            garment_type=analysis.garment_type,
            dominant_color=analysis.dominant_color,
            secondary_colors=list(getattr(analysis, "secondary_colors", [])),
            silhouette_summary=analysis.silhouette_summary,
            preserved_details=list(analysis.preserved_details),
            confidence=analysis.confidence,
        ),
        budget_max=float(parsed_budget) if isinstance(parsed_budget, Decimal) else None,
        limit=limit,
        user_country_code=user_country_code.upper() if user_country_code else None,
        user_city=user_city,
    )
    return await runtime.workflow_service.search(request)


@router.post("/api/similar-search/events/click", response_model=SimilarSearchClickEventResponse)
async def record_similar_search_click_event(
    request: SimilarSearchClickEventRequest,
    settings: Annotated[Settings, Depends(_settings)],
) -> SimilarSearchClickEventResponse | JSONResponse:
    """Record that a user opened or attempted to open one Similar Search result."""

    runtime = similar_search_runtime_dependencies(settings)
    try:
        return await runtime.click_event_service.record_click(request)
    except SimilarSearchClickEventRejected as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": exc.safe_code, "message": exc.message, "details": {}}},
        )


@router.get("/api/similar-search/redirect", response_model=None)
async def redirect_similar_search_result(
    settings: Annotated[Settings, Depends(_settings)],
    product_id: Annotated[str, Query(min_length=1, max_length=128)],
    title: Annotated[str, Query(min_length=1, max_length=255)],
    marketplace: Annotated[str, Query(min_length=1, max_length=128)],
    offer_url: Annotated[str, Query(min_length=1, max_length=2048)],
    image_url: Annotated[str | None, Query(min_length=1, max_length=2048)] = None,
    user_country_code: Annotated[str | None, Query(min_length=2, max_length=2)] = None,
    user_city: Annotated[str | None, Query(min_length=1, max_length=128)] = None,
):
    """Record one product click before redirecting to an approved external product URL."""

    runtime = similar_search_runtime_dependencies(settings)
    try:
        result = await runtime.click_event_service.record_click(
            SimilarSearchClickEventRequest(
                product_id=product_id,
                title=title,
                marketplace=marketplace,
                offer_url=offer_url,
                image_url=image_url,
                user_country_code=user_country_code,
                user_city=user_city,
            )
        )
    except SimilarSearchClickEventRejected as exc:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": exc.safe_code, "message": exc.message, "details": {}}},
        )
    if not result.redirect_allowed or result.redirect_url is None:
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "similar_search_offer_local_only",
                    "message": "This product is available only inside the local catalog right now.",
                    "details": {"event_id": result.event_id},
                }
            },
        )
    return RedirectResponse(url=result.redirect_url, status_code=302)


def _parse_optional_decimal(value: str | None) -> Decimal | None | str:
    """Parse optional form decimal without trusting browser-side validation."""

    if value is None or not value.strip():
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation:
        return "invalid"
    if parsed < 0:
        return "invalid"
    return parsed


def _validation_error(code: str, message: str) -> JSONResponse:
    """Return one structured validation error response."""

    return JSONResponse(status_code=400, content={"error": {"code": code, "message": message, "details": {}}})
