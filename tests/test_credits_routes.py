from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class _BillingServiceStub:
    async def get_account_balance(self, *, owner_id, owner_type):
        return {
            "owner_id": owner_id,
            "owner_type": owner_type,
            "available_credits": 120,
            "reserved_credits": 5,
        }

    async def list_ledger_events(self, *, owner_id, owner_type, limit=50):
        return [
            {
                "event_id": "evt-1",
                "owner_id": owner_id,
                "owner_type": owner_type,
                "event_type": "charge",
                "credits_delta": -12,
                "balance_after_event": 108,
            }
        ][:limit]


def test_get_credits_balance_returns_backend_owned_balance(monkeypatch) -> None:
    from src.entrypoints import credits_routes

    monkeypatch.setattr(
        credits_routes,
        "billing_runtime_dependencies",
        lambda settings: type("Runtime", (), {"billing_service": _BillingServiceStub()})(),
    )

    response = client.get("/api/credits/person/user-1")

    assert response.status_code == 200
    assert response.json()["available_credits"] == 120


def test_get_credits_ledger_returns_recent_events(monkeypatch) -> None:
    from src.entrypoints import credits_routes

    monkeypatch.setattr(
        credits_routes,
        "billing_runtime_dependencies",
        lambda settings: type("Runtime", (), {"billing_service": _BillingServiceStub()})(),
    )

    response = client.get("/api/credits/person/user-1/ledger")

    assert response.status_code == 200
    assert response.json()["events"][0]["event_id"] == "evt-1"
