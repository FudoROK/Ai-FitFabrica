"""FastAPI routes for backend-owned workspace bootstrap state."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from src.domain.billing import BillingOwnerType
from src.domain.workspace import WorkspaceBootstrapResponse
from src.entrypoints.runtime_dependencies import (
    billing_runtime_dependencies,
    content_package_runtime_dependencies,
    product_card_runtime_dependencies,
    try_on_runtime_dependencies,
    workspace_state_runtime_dependencies,
)
from src.settings import Settings
from src.use_cases.workspace import WorkspaceBootstrapService

router = APIRouter()


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""

    return request.app.state.settings


def _owner_id(settings: Settings) -> str:
    """Resolve the current workspace owner id with a safe fallback for tests and sandbox routes."""

    return getattr(settings, "default_person_credit_account_id", "public-person")


def _service(settings: Settings) -> WorkspaceBootstrapService:
    """Build the backend-owned workspace bootstrap service."""

    return WorkspaceBootstrapService(
        billing_service=billing_runtime_dependencies(settings).billing_service,
        owner_id=_owner_id(settings),
        owner_type=BillingOwnerType.PERSON,
        billing_enabled=bool(getattr(settings, "billing_core_enabled", False)),
        product_card_credit_cost=int(getattr(settings, "product_card_base_credit_cost", 18)),
        try_on_job_repository=try_on_runtime_dependencies(settings).job_repository,
        workspace_state_repository=workspace_state_runtime_dependencies(settings).repository,
        product_card_repository=product_card_runtime_dependencies(settings).repository,
        content_package_repository=content_package_runtime_dependencies(settings).repository,
        default_first_name="Гость",
        default_full_name="Гость FitFabrica",
    )


@router.get("/api/workspace/bootstrap", response_model=None)
async def get_workspace_bootstrap(
    settings: Annotated[Settings, Depends(_settings)],
) -> WorkspaceBootstrapResponse:
    """Return the unified workspace bootstrap payload for the web shell."""

    return await _service(settings).get_bootstrap()
