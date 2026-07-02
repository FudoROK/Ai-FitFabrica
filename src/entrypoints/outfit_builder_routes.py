"""HTTP routes for workspace outfit-builder flows."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from src.entrypoints.runtime_dependencies import workspace_state_runtime_dependencies
from src.settings import Settings
from src.use_cases.workspace.outfit_builder_brief_service import OutfitBuilderBriefService

router = APIRouter(tags=["workspace"])


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _utc_now() -> datetime:
    """Return one timezone-aware timestamp for workspace writes."""
    return datetime.now(timezone.utc)


def _service(settings: Settings) -> OutfitBuilderBriefService:
    """Build the backend-owned outfit-builder service."""
    return OutfitBuilderBriefService(
        repository=workspace_state_runtime_dependencies(settings).repository,
        clock=_utc_now,
    )


class WorkspaceOutfitBuilderBriefResponse(BaseModel):
    """Typed backend brief returned to the workspace outfit-builder UI."""

    model_config = ConfigDict(extra="forbid")

    workflow: str
    status: str
    hero_title: str
    hero_description: str
    input_sections: list[str]
    result_sections: list[str]
    readiness_note: str


class WorkspaceOutfitBuilderRequestPayload(BaseModel):
    """Typed create-request payload for the outfit-builder workflow."""

    model_config = ConfigDict(extra="forbid")

    occasion: str
    budget: str | None = None
    base_item: str | None = None


class WorkspaceOutfitBuilderRequestResponse(BaseModel):
    """Typed accepted response for an outfit-builder create request."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    workflow: str
    status: str
    occasion: str
    budget: str | None = None
    base_item: str | None = None
    message: str
    status_url: str
    created_at: str | None = None


class WorkspaceOutfitBuilderRequestListResponse(BaseModel):
    """Typed recent-requests response for the outfit-builder workflow."""

    model_config = ConfigDict(extra="forbid")

    workflow: str
    requests: list[WorkspaceOutfitBuilderRequestResponse]


class WorkspaceOutfitBuilderStatusEventResponse(BaseModel):
    """Typed status-history event for one outfit-builder request."""

    model_config = ConfigDict(extra="forbid")

    status: str
    message: str
    occurred_at: str


class WorkspaceOutfitBuilderResultSummaryResponse(BaseModel):
    """Typed result summary for one completed outfit-builder request."""

    model_config = ConfigDict(extra="forbid")

    headline: str
    summary_lines: list[str]


class WorkspaceOutfitBuilderRequestStatusResponse(BaseModel):
    """Typed backend status snapshot for one outfit-builder request."""

    model_config = ConfigDict(extra="forbid")

    request_id: str
    workflow: str
    status: str
    status_history: list[WorkspaceOutfitBuilderStatusEventResponse]
    result_summary: WorkspaceOutfitBuilderResultSummaryResponse


@router.get("/api/workspace/outfit-builder/brief", response_model=WorkspaceOutfitBuilderBriefResponse)
async def get_workspace_outfit_builder_brief(
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceOutfitBuilderBriefResponse:
    """Return the backend-owned outfit-builder brief for the workspace screen."""
    brief = await _service(settings).get_brief()
    return WorkspaceOutfitBuilderBriefResponse.model_validate(brief)


@router.get("/api/workspace/outfit-builder/requests", response_model=WorkspaceOutfitBuilderRequestListResponse)
async def get_workspace_outfit_builder_requests(
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceOutfitBuilderRequestListResponse:
    """Return recent backend-owned outfit-builder requests for the workspace screen."""
    requests = await _service(settings).list_recent_requests()
    return WorkspaceOutfitBuilderRequestListResponse(
        workflow="outfit_builder",
        requests=[WorkspaceOutfitBuilderRequestResponse.model_validate(item) for item in requests],
    )


@router.get(
    "/api/workspace/outfit-builder/requests/{request_id}/status",
    response_model=WorkspaceOutfitBuilderRequestStatusResponse,
)
async def get_workspace_outfit_builder_request_status(
    request_id: str,
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceOutfitBuilderRequestStatusResponse:
    """Return one backend-owned status snapshot for the requested outfit-builder request."""
    try:
        request_status = await _service(settings).get_request_status(request_id=request_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=f"Outfit-builder request not found: {request_id}") from error
    return WorkspaceOutfitBuilderRequestStatusResponse.model_validate(request_status)


@router.post("/api/workspace/outfit-builder/requests", response_model=WorkspaceOutfitBuilderRequestResponse, status_code=202)
async def create_workspace_outfit_builder_request(
    payload: WorkspaceOutfitBuilderRequestPayload,
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceOutfitBuilderRequestResponse:
    """Accept one typed outfit-builder request from the workspace UI."""
    request = await _service(settings).create_request(
        occasion=payload.occasion,
        budget=payload.budget,
        base_item=payload.base_item,
    )
    return WorkspaceOutfitBuilderRequestResponse.model_validate(request)
