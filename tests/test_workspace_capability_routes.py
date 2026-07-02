from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)

DENIED_REASON = "Подключите магазин в integrations, чтобы сервер разрешил publish, import и sync."


class _CapabilityServiceStub:
    async def build_snapshot(self, *, owner_id: str):
        return {
            "business_profile": {"exists": True, "display_name": "FitFabrica Studio", "channels": ["wildberries"]},
            "integrations": {"has_connected_store": False, "connected_channels": []},
            "capability_states": [
                {"capability": "business_templates", "enabled": True, "disabled_reason": None},
                {
                    "capability": "marketplace_publish",
                    "enabled": False,
                    "disabled_reason": DENIED_REASON,
                },
            ],
            "enabled_capabilities": ["business_templates"],
        }

    async def require_capability(self, *, owner_id: str, capability: str):
        if capability == "business_templates":
            return None

        from src.use_cases.workspace.capability_service import WorkspaceCapabilityDeniedError

        raise WorkspaceCapabilityDeniedError(capability=capability, reason=DENIED_REASON)


class _CapabilityServicePublishEnabledStub(_CapabilityServiceStub):
    async def build_snapshot(self, *, owner_id: str):
        return {
            "business_profile": {"exists": True, "display_name": "FitFabrica Studio", "channels": ["wildberries"]},
            "integrations": {"has_connected_store": True, "connected_channels": ["wildberries"]},
            "capability_states": [
                {"capability": "marketplace_publish", "enabled": True, "disabled_reason": None},
                {"capability": "catalog_import", "enabled": True, "disabled_reason": None},
                {"capability": "catalog_sync", "enabled": True, "disabled_reason": None},
            ],
            "enabled_capabilities": ["marketplace_publish", "catalog_import", "catalog_sync"],
        }

    async def require_capability(self, *, owner_id: str, capability: str):
        return None


def test_workspace_capability_route_returns_server_capability_matrix(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServiceStub(),
    )

    response = client.get("/api/workspace/capabilities")

    assert response.status_code == 200
    payload = response.json()
    assert payload["enabled_capabilities"] == ["business_templates"]
    publish_gate = next(item for item in payload["capability_states"] if item["capability"] == "marketplace_publish")
    assert publish_gate["enabled"] is False


def test_workspace_capability_assert_route_returns_no_content_when_enabled(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServiceStub(),
    )

    response = client.post("/api/workspace/capabilities/business_templates/assert")

    assert response.status_code == 204


def test_workspace_capability_assert_route_returns_403_with_reason(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServiceStub(),
    )

    response = client.post("/api/workspace/capabilities/marketplace_publish/assert")

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "workspace_capability_denied",
            "message": DENIED_REASON,
            "details": {"capability": "marketplace_publish"},
        }
    }


def test_workspace_marketplace_publish_action_returns_accepted_when_capability_is_open(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServicePublishEnabledStub(),
    )

    response = client.post(
        "/api/workspace/actions/marketplace-publish",
        json={
            "target_channel": "wildberries",
            "product_card_version_id": "product_card_123_v1",
            "content_package_version_id": "content_package_123_v1",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "action": "marketplace_publish",
        "status": "accepted",
        "target_channel": "wildberries",
        "product_card_version_id": "product_card_123_v1",
        "content_package_version_id": "content_package_123_v1",
        "message": "Capability guard passed. Real publish pipeline is not wired yet.",
    }


def test_workspace_marketplace_publish_action_returns_403_when_capability_is_closed(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServiceStub(),
    )

    response = client.post(
        "/api/workspace/actions/marketplace-publish",
        json={
            "target_channel": "wildberries",
            "product_card_version_id": "product_card_123_v1",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "workspace_capability_denied",
            "message": DENIED_REASON,
            "details": {"capability": "marketplace_publish"},
        }
    }


def test_workspace_catalog_import_action_returns_accepted_when_capability_is_open(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServicePublishEnabledStub(),
    )

    response = client.post(
        "/api/workspace/actions/catalog-import",
        json={
            "target_channel": "wildberries",
            "catalog_source": "merchant_feed",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "action": "catalog_import",
        "status": "accepted",
        "target_channel": "wildberries",
        "catalog_source": "merchant_feed",
        "message": "Capability guard passed. Real catalog import pipeline is not wired yet.",
    }


def test_workspace_catalog_import_action_returns_403_when_capability_is_closed(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServiceStub(),
    )

    response = client.post(
        "/api/workspace/actions/catalog-import",
        json={
            "target_channel": "wildberries",
            "catalog_source": "merchant_feed",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "workspace_capability_denied",
            "message": DENIED_REASON,
            "details": {"capability": "catalog_import"},
        }
    }


def test_workspace_catalog_sync_action_returns_accepted_when_capability_is_open(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServicePublishEnabledStub(),
    )

    response = client.post(
        "/api/workspace/actions/catalog-sync",
        json={
            "target_channel": "wildberries",
            "sync_scope": "full",
        },
    )

    assert response.status_code == 202
    assert response.json() == {
        "action": "catalog_sync",
        "status": "accepted",
        "target_channel": "wildberries",
        "sync_scope": "full",
        "message": "Capability guard passed. Real catalog sync pipeline is not wired yet.",
    }


def test_workspace_catalog_sync_action_returns_403_when_capability_is_closed(monkeypatch) -> None:
    from src.entrypoints import workspace_capability_routes

    monkeypatch.setattr(
        workspace_capability_routes,
        "workspace_capability_service",
        lambda settings: _CapabilityServiceStub(),
    )

    response = client.post(
        "/api/workspace/actions/catalog-sync",
        json={
            "target_channel": "wildberries",
            "sync_scope": "full",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "workspace_capability_denied",
            "message": DENIED_REASON,
            "details": {"capability": "catalog_sync"},
        }
    }
