from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient


def _client(*, enabled: bool, admin_api_token: str | None = "test-admin-token") -> TestClient:
    from src.entrypoints.admin_cost_routes import router

    app = FastAPI()
    app.state.settings = type(
        "Settings",
        (),
        {
            "enable_admin_costs": enabled,
            "admin_api_token": admin_api_token,
            "allow_unsafe_admin_header_auth": False,
            "try_on_base_credit_cost": 12,
            "product_card_base_credit_cost": 18,
            "content_package_base_credit_cost": 14,
            "pricing_base_credit_cost": 6,
        },
    )()
    app.include_router(router)
    return TestClient(app)


def _headers() -> dict[str, str]:
    return {"authorization": "Bearer test-admin-token"}


def test_admin_cost_routes_are_disabled_by_default() -> None:
    client = _client(enabled=False)

    response = client.get("/api/admin/costs/baseline", headers=_headers())

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "admin_costs_disabled"


def test_admin_cost_routes_require_bearer_token() -> None:
    client = _client(enabled=True)

    response = client.get("/api/admin/costs/baseline")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "admin_auth_invalid"


def test_admin_cost_baseline_returns_safe_pricing_and_credit_config() -> None:
    client = _client(enabled=True)

    response = client.get("/api/admin/costs/baseline", headers=_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["credit_value_kzt"] == "50"
    assert payload["usd_to_kzt"] == "500"
    assert payload["workflow_credit_costs"]["try_on"] == 12
    assert payload["workflow_credit_costs"]["product_card"] == 18
    assert payload["provider_price_config_version"].startswith("provider_prices.")
    assert payload["provider_prices"]
    assert payload["pricing_recommendations"]
    assert payload["guardrails"]["live_billing_changed"] is False
    assert payload["guardrails"]["frontend_may_calculate_credits"] is False
    assert "test-admin-token" not in response.text
