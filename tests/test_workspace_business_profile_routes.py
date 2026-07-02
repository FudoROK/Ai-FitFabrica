from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class _BusinessProfileServiceStub:
    async def save_business_profile(self, *, request):
        return {
            "owner_id": request.owner_id,
            "display_name": request.display_name,
            "channels": list(request.channels),
            "created_at": "2026-06-12T00:00:00+00:00",
            "updated_at": "2026-06-12T00:00:00+00:00",
        }

    async def get_business_profile(self, *, owner_id: str):
        return {
            "owner_id": owner_id,
            "display_name": "FitFabrica Studio",
            "channels": ["instagram", "wildberries"],
            "created_at": "2026-06-12T00:00:00+00:00",
            "updated_at": "2026-06-12T00:00:00+00:00",
        }


def test_workspace_business_profile_route_saves_structured_state(monkeypatch) -> None:
    from src.entrypoints import workspace_profile_routes

    monkeypatch.setattr(
        workspace_profile_routes,
        "workspace_business_profile_service",
        lambda settings: _BusinessProfileServiceStub(),
    )

    response = client.post(
        "/api/workspace/business-profile",
        json={
            "display_name": "FitFabrica Studio",
            "channels": ["instagram", "wildberries"],
        },
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "FitFabrica Studio"
    assert response.json()["channels"] == ["instagram", "wildberries"]


def test_workspace_business_profile_route_returns_current_profile(monkeypatch) -> None:
    from src.entrypoints import workspace_profile_routes

    monkeypatch.setattr(
        workspace_profile_routes,
        "workspace_business_profile_service",
        lambda settings: _BusinessProfileServiceStub(),
    )

    response = client.get("/api/workspace/business-profile")

    assert response.status_code == 200
    assert response.json()["display_name"] == "FitFabrica Studio"
