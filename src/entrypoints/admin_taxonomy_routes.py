"""Admin-only taxonomy review API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.domain.garment_taxonomy import GarmentTaxonomyCandidate, GarmentTaxonomyCandidateStatus
from src.entrypoints.admin_auth import AdminActor, resolve_admin_actor
from src.entrypoints.runtime_dependencies import garment_taxonomy_service
from src.settings import Settings

router = APIRouter(prefix="/api/admin/taxonomy", tags=["admin-taxonomy"])


class TaxonomyCandidatesResponse(BaseModel):
    """Admin taxonomy candidate list response."""

    model_config = ConfigDict(extra="forbid")

    candidates: list[GarmentTaxonomyCandidate]


class TaxonomyCandidateMutationResponse(BaseModel):
    """Admin taxonomy mutation response."""

    model_config = ConfigDict(extra="forbid")

    candidate: GarmentTaxonomyCandidate


class RejectCandidatePayload(BaseModel):
    """Admin reject request payload."""

    model_config = ConfigDict(extra="forbid")

    review_reason: str = Field(min_length=1)


class MergeCandidatePayload(BaseModel):
    """Admin merge request payload."""

    model_config = ConfigDict(extra="forbid")

    target_catalog_item_code: str = Field(min_length=1)


class RenameAndApproveCandidatePayload(BaseModel):
    """Admin rename-and-approve request payload."""

    model_config = ConfigDict(extra="forbid")

    approved_catalog_item_code: str = Field(min_length=1)
    approved_display_name: str = Field(min_length=1)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _admin_actor(
    settings: Settings,
    authorization: str | None,
    admin_role: str | None,
    admin_id: str | None,
) -> AdminActor | JSONResponse:
    """Validate admin taxonomy feature flag and role headers."""
    if not bool(getattr(settings, "enable_admin_taxonomy", False)):
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "admin_taxonomy_disabled", "message": "Admin taxonomy API is disabled."}},
        )
    return resolve_admin_actor(
        settings=settings,
        allowed_roles={"admin", "taxonomy_admin"},
        authorization=authorization,
        legacy_admin_role=admin_role,
        legacy_admin_id=admin_id,
    )


def _service_or_error(settings: Settings):
    service = garment_taxonomy_service(settings)
    if service is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "admin_taxonomy_storage_unavailable",
                    "message": "Garment taxonomy storage is not configured.",
                }
            },
        )
    return service


def _validation_error_response(exc: ValueError) -> JSONResponse:
    """Return one structured response for admin taxonomy validation failures."""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "admin_taxonomy_validation_failed",
                "message": str(exc),
            }
        },
    )


@router.get("/candidates", response_model=TaxonomyCandidatesResponse)
async def list_taxonomy_candidates(
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> TaxonomyCandidatesResponse | JSONResponse:
    """List pending taxonomy candidates for admin review."""
    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    candidates = await service.list_candidates(status=GarmentTaxonomyCandidateStatus.PENDING_REVIEW)
    return TaxonomyCandidatesResponse(candidates=candidates)


@router.post("/candidates/{candidate_id}/approve", response_model=TaxonomyCandidateMutationResponse)
async def approve_taxonomy_candidate(
    candidate_id: str,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> TaxonomyCandidateMutationResponse | JSONResponse:
    """Approve one taxonomy candidate into the production catalog."""
    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        candidate = await service.approve_candidate(candidate_id=candidate_id, actor_id=actor.actor_id)
    except ValueError as exc:
        return _validation_error_response(exc)
    return TaxonomyCandidateMutationResponse(candidate=candidate)


@router.post("/candidates/{candidate_id}/reject", response_model=TaxonomyCandidateMutationResponse)
async def reject_taxonomy_candidate(
    candidate_id: str,
    payload: RejectCandidatePayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> TaxonomyCandidateMutationResponse | JSONResponse:
    """Reject one taxonomy candidate with an explicit reason."""
    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        candidate = await service.reject_candidate(
            candidate_id=candidate_id,
            actor_id=actor.actor_id,
            review_reason=payload.review_reason,
        )
    except ValueError as exc:
        return _validation_error_response(exc)
    return TaxonomyCandidateMutationResponse(candidate=candidate)


@router.post("/candidates/{candidate_id}/merge", response_model=TaxonomyCandidateMutationResponse)
async def merge_taxonomy_candidate(
    candidate_id: str,
    payload: MergeCandidatePayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> TaxonomyCandidateMutationResponse | JSONResponse:
    """Merge one taxonomy candidate into an existing catalog item."""
    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        candidate = await service.merge_candidate(
            candidate_id=candidate_id,
            actor_id=actor.actor_id,
            target_catalog_item_code=payload.target_catalog_item_code,
        )
    except ValueError as exc:
        return _validation_error_response(exc)
    return TaxonomyCandidateMutationResponse(candidate=candidate)


@router.post("/candidates/{candidate_id}/rename-and-approve", response_model=TaxonomyCandidateMutationResponse)
async def rename_and_approve_taxonomy_candidate(
    candidate_id: str,
    payload: RenameAndApproveCandidatePayload,
    settings: Annotated[Settings, Depends(_settings)],
    authorization: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_role: Annotated[str | None, Header()] = None,
    x_fitfabrica_admin_id: Annotated[str | None, Header()] = None,
) -> TaxonomyCandidateMutationResponse | JSONResponse:
    """Approve one taxonomy candidate under an admin-selected code and display name."""
    actor = _admin_actor(settings, authorization, x_fitfabrica_admin_role, x_fitfabrica_admin_id)
    if isinstance(actor, JSONResponse):
        return actor
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service
    try:
        candidate = await service.rename_and_approve_candidate(
            candidate_id=candidate_id,
            actor_id=actor.actor_id,
            approved_catalog_item_code=payload.approved_catalog_item_code,
            approved_display_name=payload.approved_display_name,
        )
    except ValueError as exc:
        return _validation_error_response(exc)
    return TaxonomyCandidateMutationResponse(candidate=candidate)
