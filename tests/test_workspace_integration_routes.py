from __future__ import annotations

from fastapi.testclient import TestClient

from src.domain.workspace_state import WorkspaceIntegrationState
from src.main import app

client = TestClient(app)


class _IntegrationServiceStub:
    async def save_integrations(self, *, request):
        return {
            "owner_id": request.owner_id,
            "connected_channels": list(request.connected_channels),
            "has_connected_store": request.has_connected_store,
            "created_at": "2026-06-12T00:00:00+00:00",
            "updated_at": "2026-06-12T00:00:00+00:00",
        }

    async def get_integrations(self, *, owner_id: str):
        return WorkspaceIntegrationState(
            owner_id=owner_id,
            connected_channels=["wildberries"],
            has_connected_store=True,
            created_at="2026-06-12T00:00:00+00:00",
            updated_at="2026-06-12T00:00:00+00:00",
        )


def test_workspace_integrations_route_saves_structured_state(monkeypatch) -> None:
    from src.entrypoints import workspace_integration_routes

    monkeypatch.setattr(
        workspace_integration_routes,
        "workspace_integration_service",
        lambda settings: _IntegrationServiceStub(),
    )

    response = client.post(
        "/api/workspace/integrations",
        json={
            "connected_channels": ["wildberries"],
            "has_connected_store": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["connected_channels"] == ["wildberries"]
    assert response.json()["has_connected_store"] is True


def test_workspace_integrations_route_returns_current_state(monkeypatch) -> None:
    from src.entrypoints import workspace_integration_routes

    monkeypatch.setattr(
        workspace_integration_routes,
        "workspace_integration_service",
        lambda settings: _IntegrationServiceStub(),
    )

    response = client.get("/api/workspace/integrations")

    assert response.status_code == 200
    assert response.json()["connected_channels"] == ["wildberries"]
    assert response.json()["has_connected_store"] is True
