"""Workspace integrations API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from src.entrypoints.runtime_dependencies import workspace_integration_service
from src.settings import load_settings
from src.use_cases.workspace.integration_service import WorkspaceIntegrationRequest

router = APIRouter(tags=["workspace"])


class WorkspaceIntegrationsPayload(BaseModel):
    """Typed payload used to persist workspace integrations state."""

    model_config = ConfigDict(extra="forbid")

    connected_channels: list[str] = Field(default_factory=list)
    has_connected_store: bool = False


class WorkspaceIntegrationsResponse(BaseModel):
    """HTTP response for persisted workspace integrations state."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    owner_id: str
    connected_channels: list[str]
    has_connected_store: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None


@router.post("/api/workspace/integrations", response_model=WorkspaceIntegrationsResponse)
async def save_workspace_integrations(payload: WorkspaceIntegrationsPayload) -> WorkspaceIntegrationsResponse:
    """Persist backend-owned workspace integrations state."""
    settings = load_settings()
    owner_id = getattr(settings, "default_person_credit_account_id", "public-person")
    state = await workspace_integration_service(settings).save_integrations(
        request=WorkspaceIntegrationRequest(
            owner_id=owner_id,
            connected_channels=payload.connected_channels,
            has_connected_store=payload.has_connected_store,
        )
    )
    return WorkspaceIntegrationsResponse.model_validate(state)


@router.get("/api/workspace/integrations", response_model=WorkspaceIntegrationsResponse)
async def get_workspace_integrations() -> WorkspaceIntegrationsResponse:
    """Return current backend-owned workspace integrations state."""
    settings = load_settings()
    owner_id = getattr(settings, "default_person_credit_account_id", "public-person")
    state = await workspace_integration_service(settings).get_integrations(owner_id=owner_id)
    return WorkspaceIntegrationsResponse.model_validate(state)
