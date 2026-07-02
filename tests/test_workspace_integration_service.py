from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.domain.workspace_state import WorkspaceIntegrationState
from src.use_cases.workspace.integration_service import WorkspaceIntegrationRequest, WorkspaceIntegrationService


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class _RepositoryStub:
    async def upsert_integrations(self, *, request: WorkspaceIntegrationRequest, now: datetime) -> WorkspaceIntegrationState:
        return WorkspaceIntegrationState(
            owner_id=request.owner_id,
            connected_channels=list(request.connected_channels),
            has_connected_store=request.has_connected_store,
            created_at=now,
            updated_at=now,
        )

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        return WorkspaceIntegrationState(
            owner_id=owner_id,
            connected_channels=["wildberries", "ozon"],
            has_connected_store=True,
            created_at=_utc_now(),
            updated_at=_utc_now(),
        )


@pytest.mark.asyncio
async def test_workspace_integration_service_saves_state() -> None:
    service = WorkspaceIntegrationService(repository=_RepositoryStub(), clock=_utc_now)

    result = await service.save_integrations(
        request=WorkspaceIntegrationRequest(
            owner_id="public-person",
            connected_channels=["wildberries", "ozon"],
            has_connected_store=True,
        )
    )

    assert result.owner_id == "public-person"
    assert result.connected_channels == ["wildberries", "ozon"]
    assert result.has_connected_store is True


@pytest.mark.asyncio
async def test_workspace_integration_service_reads_state() -> None:
    service = WorkspaceIntegrationService(repository=_RepositoryStub(), clock=_utc_now)

    result = await service.get_integrations(owner_id="public-person")

    assert result.owner_id == "public-person"
    assert result.connected_channels == ["wildberries", "ozon"]
    assert result.has_connected_store is True
