"""Workspace capability matrix API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from src.domain.workspace import WorkspaceCapabilityMatrixResponse
from src.entrypoints.runtime_dependencies import workspace_capability_service
from src.settings import Settings
from src.use_cases.workspace.capability_service import WorkspaceCapabilityDeniedError

router = APIRouter(tags=["workspace"])


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _owner_id(settings: Settings) -> str:
    """Resolve the workspace owner id used by capability checks."""
    return getattr(settings, "default_person_credit_account_id", "public-person")


def _capability_denied_response(error: WorkspaceCapabilityDeniedError) -> JSONResponse:
    """Translate domain capability denial into a structured API error."""
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "workspace_capability_denied",
                "message": error.reason,
                "details": {"capability": error.capability},
            }
        },
    )


async def _require_capability(settings: Settings, capability: str) -> None | JSONResponse:
    """Return a structured 403 response when a capability is not enabled."""
    try:
        await workspace_capability_service(settings).require_capability(
            owner_id=_owner_id(settings),
            capability=capability,
        )
    except WorkspaceCapabilityDeniedError as error:
        return _capability_denied_response(error)
    return None


class WorkspaceMarketplacePublishPayload(BaseModel):
    """Typed sandbox publish-action payload guarded by workspace capabilities."""

    model_config = ConfigDict(extra="forbid")

    target_channel: str = Field(min_length=1)
    product_card_version_id: str = Field(min_length=1)
    content_package_version_id: str | None = None


class WorkspaceMarketplacePublishResponse(BaseModel):
    """Structured accepted response for the guarded marketplace publish action."""

    model_config = ConfigDict(extra="forbid")

    action: str
    status: str
    target_channel: str
    product_card_version_id: str
    content_package_version_id: str | None = None
    message: str


class WorkspaceCatalogImportPayload(BaseModel):
    """Typed sandbox catalog-import payload guarded by workspace capabilities."""

    model_config = ConfigDict(extra="forbid")

    target_channel: str = Field(min_length=1)
    catalog_source: str = Field(min_length=1)


class WorkspaceCatalogImportResponse(BaseModel):
    """Structured accepted response for the guarded catalog import action."""

    model_config = ConfigDict(extra="forbid")

    action: str
    status: str
    target_channel: str
    catalog_source: str
    message: str


class WorkspaceCatalogSyncPayload(BaseModel):
    """Typed sandbox catalog-sync payload guarded by workspace capabilities."""

    model_config = ConfigDict(extra="forbid")

    target_channel: str = Field(min_length=1)
    sync_scope: str = Field(min_length=1)


class WorkspaceCatalogSyncResponse(BaseModel):
    """Structured accepted response for the guarded catalog sync action."""

    model_config = ConfigDict(extra="forbid")

    action: str
    status: str
    target_channel: str
    sync_scope: str
    message: str


@router.get("/api/workspace/capabilities", response_model=WorkspaceCapabilityMatrixResponse)
async def get_workspace_capabilities(
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceCapabilityMatrixResponse:
    """Return the backend-owned capability matrix for the current workspace owner."""
    return await workspace_capability_service(settings).build_snapshot(owner_id=_owner_id(settings))


@router.post("/api/workspace/capabilities/{capability}/assert", status_code=204)
async def assert_workspace_capability(
    capability: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return 204 when the requested capability is enabled, otherwise a structured 403."""
    denied = await _require_capability(settings, capability)
    if denied is not None:
        return denied
    return Response(status_code=204)


@router.post("/api/workspace/actions/marketplace-publish", response_model=WorkspaceMarketplacePublishResponse, status_code=202)
async def create_marketplace_publish_action(
    payload: WorkspaceMarketplacePublishPayload,
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceMarketplacePublishResponse | JSONResponse:
    """Accept one guarded marketplace-publish intent after capability verification."""
    denied = await _require_capability(settings, "marketplace_publish")
    if denied is not None:
        return denied

    return WorkspaceMarketplacePublishResponse(
        action="marketplace_publish",
        status="accepted",
        target_channel=payload.target_channel,
        product_card_version_id=payload.product_card_version_id,
        content_package_version_id=payload.content_package_version_id,
        message="Capability guard passed. Real publish pipeline is not wired yet.",
    )


@router.post("/api/workspace/actions/catalog-import", response_model=WorkspaceCatalogImportResponse, status_code=202)
async def create_catalog_import_action(
    payload: WorkspaceCatalogImportPayload,
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceCatalogImportResponse | JSONResponse:
    """Accept one guarded catalog-import intent after capability verification."""
    denied = await _require_capability(settings, "catalog_import")
    if denied is not None:
        return denied

    return WorkspaceCatalogImportResponse(
        action="catalog_import",
        status="accepted",
        target_channel=payload.target_channel,
        catalog_source=payload.catalog_source,
        message="Capability guard passed. Real catalog import pipeline is not wired yet.",
    )


@router.post("/api/workspace/actions/catalog-sync", response_model=WorkspaceCatalogSyncResponse, status_code=202)
async def create_catalog_sync_action(
    payload: WorkspaceCatalogSyncPayload,
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceCatalogSyncResponse | JSONResponse:
    """Accept one guarded catalog-sync intent after capability verification."""
    denied = await _require_capability(settings, "catalog_sync")
    if denied is not None:
        return denied

    return WorkspaceCatalogSyncResponse(
        action="catalog_sync",
        status="accepted",
        target_channel=payload.target_channel,
        sync_scope=payload.sync_scope,
        message="Capability guard passed. Real catalog sync pipeline is not wired yet.",
    )
