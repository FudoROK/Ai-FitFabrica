"""Tests for public website form backend routes."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.entrypoints.http_routes import build_http_router
from src.entrypoints.public_request_routes import router


class _Settings:
    """Minimal settings object for public request route tests."""

    postgres_dsn = None


def _client() -> TestClient:
    """Build a route test client with local in-memory persistence."""

    app = FastAPI()
    app.state.settings = _Settings()
    app.include_router(router)
    return TestClient(app)


def _http_client() -> TestClient:
    """Build the full HTTP router client with local in-memory persistence."""

    app = FastAPI()
    app.state.settings = _Settings()
    app.include_router(build_http_router())
    return TestClient(app)


def test_demo_request_route_persists_public_request() -> None:
    client = _client()

    response = client.post(
        "/demo-request",
        json={
            "name": "Madi",
            "email": "madi@example.com",
            "company": "FitFabrica Test",
            "message": "Need B2B catalog demo",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["request_id"].startswith("demo_req_")
    assert payload["status"] == "received"


def test_public_routes_are_registered_on_full_http_router() -> None:
    client = _http_client()

    response = client.post(
        "/demo-request",
        json={
            "name": "Madi",
            "email": "madi@example.com",
            "message": "Need a prepared no-billing contact flow",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_sign_in_route_fails_closed_until_auth_is_configured() -> None:
    client = _client()

    response = client.post("/auth/sign-in", json={"email": "madi@example.com", "password": "secret"})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "auth_not_configured"
    assert "secret" not in response.text
