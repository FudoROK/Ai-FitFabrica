"""FastAPI routes for persisted workspace business-profile state."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from src.settings import Settings
from src.use_cases.workspace import WorkspaceBusinessProfileRequest
from src.entrypoints.runtime_dependencies import workspace_business_profile_service

router = APIRouter()


class WorkspaceBusinessProfilePayload(BaseModel):
    """Typed payload for business-profile persistence."""

    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1)
    channels: list[str] = Field(default_factory=list)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _owner_id(settings: Settings) -> str:
    """Resolve the current workspace owner id with a safe fallback for tests and sandbox routes."""

    return getattr(settings, "default_person_credit_account_id", "public-person")


@router.post("/api/workspace/business-profile")
async def save_workspace_business_profile(
    payload: WorkspaceBusinessProfilePayload,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Persist one backend-owned business profile for the current workspace owner."""
    service = workspace_business_profile_service(settings)
    return await service.save_business_profile(
        request=WorkspaceBusinessProfileRequest(
            owner_id=_owner_id(settings),
            display_name=payload.display_name,
            channels=list(payload.channels),
        )
    )


@router.get("/api/workspace/business-profile")
async def get_workspace_business_profile(
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the persisted backend-owned business profile for the current workspace owner."""
    service = workspace_business_profile_service(settings)
    profile = await service.get_business_profile(owner_id=_owner_id(settings))
    if profile is None:
        raise HTTPException(status_code=404, detail="workspace_business_profile_not_found")
    return profile
