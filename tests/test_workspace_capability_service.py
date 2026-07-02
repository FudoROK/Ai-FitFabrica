from __future__ import annotations

import pytest

from src.domain.workspace_state import WorkspaceBusinessProfileState, WorkspaceIntegrationState
from src.use_cases.workspace.capability_service import WorkspaceCapabilityDeniedError, WorkspaceCapabilityService


class _WorkspaceStateRepositoryStub:
    def __init__(
        self,
        *,
        profile: WorkspaceBusinessProfileState | None,
        integrations: WorkspaceIntegrationState,
    ) -> None:
        self._profile = profile
        self._integrations = integrations

    async def get_business_profile(self, *, owner_id: str) -> WorkspaceBusinessProfileState | None:
        assert owner_id == "public-person"
        return self._profile

    async def get_integrations(self, *, owner_id: str) -> WorkspaceIntegrationState:
        assert owner_id == "public-person"
        return self._integrations


@pytest.mark.asyncio
async def test_workspace_capability_service_enables_b2b_publish_flow_only_with_profile_and_store() -> None:
    service = WorkspaceCapabilityService(
        repository=_WorkspaceStateRepositoryStub(
            profile=WorkspaceBusinessProfileState(
                owner_id="public-person",
                display_name="FitFabrica Studio",
                channels=["wildberries"],
            ),
            integrations=WorkspaceIntegrationState(
                owner_id="public-person",
                connected_channels=["wildberries"],
                has_connected_store=True,
            ),
        )
    )

    snapshot = await service.build_snapshot(owner_id="public-person")

    assert snapshot.business_profile.exists is True
    assert snapshot.integrations.has_connected_store is True
    assert "business_templates" in snapshot.enabled_capabilities
    assert "marketplace_publish" in snapshot.enabled_capabilities
    assert "catalog_import" in snapshot.enabled_capabilities
    assert "catalog_sync" in snapshot.enabled_capabilities


@pytest.mark.asyncio
async def test_workspace_capability_service_returns_disabled_reason_without_store() -> None:
    service = WorkspaceCapabilityService(
        repository=_WorkspaceStateRepositoryStub(
            profile=WorkspaceBusinessProfileState(
                owner_id="public-person",
                display_name="FitFabrica Studio",
                channels=["instagram"],
            ),
            integrations=WorkspaceIntegrationState(
                owner_id="public-person",
                connected_channels=[],
                has_connected_store=False,
            ),
        )
    )

    snapshot = await service.build_snapshot(owner_id="public-person")
    publish_gate = next(item for item in snapshot.capability_states if item.capability == "marketplace_publish")

    assert publish_gate.enabled is False
    assert publish_gate.disabled_reason == "Подключите магазин в integrations, чтобы сервер разрешил publish, import и sync."


@pytest.mark.asyncio
async def test_workspace_capability_service_rejects_missing_capability() -> None:
    service = WorkspaceCapabilityService(
        repository=_WorkspaceStateRepositoryStub(
            profile=None,
            integrations=WorkspaceIntegrationState(
                owner_id="public-person",
                connected_channels=[],
                has_connected_store=False,
            ),
        )
    )

    with pytest.raises(WorkspaceCapabilityDeniedError) as error:
        await service.require_capability(owner_id="public-person", capability="marketplace_publish")

    assert error.value.capability == "marketplace_publish"
    assert error.value.reason == "Сначала сохраните business profile и подключите магазин, чтобы backend открыл publish, import и sync."
