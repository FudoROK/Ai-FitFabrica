from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class _WorkspaceBootstrapServiceStub:
    async def get_bootstrap(self):
        return {
            "user": {"first_name": "Гость", "full_name": "Гость FitFabrica"},
            "credit_owner": {"owner_id": "public-person", "owner_type": "person"},
            "credits": {
                "balance": 120,
                "currency": "credits",
                "low_balance_threshold": 12,
                "billing_enabled": False,
            },
            "business_profile": {"exists": False, "display_name": None, "channels": []},
            "integrations": {"has_connected_store": False, "connected_channels": []},
            "capabilities": [
                "try_on_create",
                "outfit_builder_create",
                "similar_search_create",
                "product_card_create",
                "business_profile_manage",
                "business_templates",
                "manual_export",
                "marketplace_publish",
                "catalog_import",
                "catalog_sync",
            ],
            "quick_actions": [
                {
                    "id": "try-on",
                    "label": "Новая примерка",
                    "description": "Запуск try-on workflow.",
                    "href": "/workspace/new-fitting",
                    "capability": "try_on_create",
                    "enabled": True,
                    "disabled_reason": None,
                }
            ],
            "recent_jobs": [
                {
                    "job_id": "outfit_req_001",
                    "workflow_type": "outfit_builder",
                    "title": "Подбор образа outfit_req_001",
                    "status": "completed",
                    "href": "/workspace/outfit-builder",
                    "updated_at": "2026-06-12T10:00:00Z",
                    "summary": "Outfit recommendations are ready for review.",
                }
            ],
        }


def test_workspace_bootstrap_returns_backend_owned_shell_state(monkeypatch) -> None:
    from src.entrypoints import workspace_routes

    monkeypatch.setattr(
        workspace_routes,
        "_service",
        lambda _settings: _WorkspaceBootstrapServiceStub(),
    )

    response = client.get("/api/workspace/bootstrap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["credit_owner"]["owner_id"] == "public-person"
    assert payload["credits"]["balance"] == 120
    assert "manual_export" in payload["capabilities"]
    assert "marketplace_publish" in payload["capabilities"]
    assert payload["integrations"]["has_connected_store"] is False
    assert payload["recent_jobs"][0]["workflow_type"] == "outfit_builder"
