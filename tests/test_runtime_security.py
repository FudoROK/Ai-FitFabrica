from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import pytest

from src.entrypoints import policies
from src.main import app
from src.settings import Settings


def _base_settings(**overrides) -> Settings:
    payload = {
        "_env_file": None,
        "GCP_PROJECT_ID": "test-project",
        "PUBSUB_TOPIC_NAME": "test-topic",
        "VERTEX_PROJECT": "test-project",
        "VERTEX_AGENT_RESOURCE": "test-agent",
        "HUBSPOT_ACCESS_TOKEN": "test-hubspot-token",
        "ENVIRONMENT": "test",
        "PUBLIC_STATUS_ENDPOINTS_ENABLED": False,
        "STATUS_ENDPOINT_TOKEN": "status-token",
    }
    payload.update(overrides)
    return Settings(**payload)


@pytest.fixture(autouse=True)
def _restore_app_settings():
    original = app.state.settings
    yield
    app.state.settings = original


def test_has_valid_token_uses_constant_time_compare(monkeypatch):
    captured = {}

    def _compare(left: str, right: str) -> bool:
        captured["pair"] = (left, right)
        return True

    monkeypatch.setattr(policies.hmac, "compare_digest", _compare)

    token_app = FastAPI()

    @token_app.get("/")
    async def _probe(request: Request):
        return {"authorized": policies.has_valid_token(request, "status-token", "X-Test-Token")}

    response = TestClient(token_app).get("/", headers={"X-Test-Token": "status-token"})

    assert response.status_code == 200
    assert response.json() == {"authorized": True}
    assert captured["pair"] == ("status-token", "status-token")


@pytest.mark.parametrize("endpoint", ["/health", "/time"])
def test_status_endpoints_reject_non_loopback_without_token(endpoint):
    app.state.settings = _base_settings()

    response = TestClient(app).get(endpoint)

    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}


@pytest.mark.parametrize("endpoint", ["/health", "/time"])
def test_status_endpoints_accept_valid_status_token(endpoint):
    app.state.settings = _base_settings()

    response = TestClient(app).get(endpoint, headers={"X-Status-Token": "status-token"})

    assert response.status_code == 200


@pytest.mark.parametrize("endpoint", ["/health", "/time"])
def test_status_endpoints_allow_public_opt_in(endpoint):
    app.state.settings = _base_settings(PUBLIC_STATUS_ENDPOINTS_ENABLED=True, STATUS_ENDPOINT_TOKEN=None)

    response = TestClient(app).get(endpoint)

    assert response.status_code == 200


@pytest.mark.parametrize("endpoint", ["/health", "/time"])
def test_status_endpoints_allow_loopback_without_token(endpoint):
    app.state.settings = _base_settings()

    response = TestClient(app, client=("127.0.0.1", 50000)).get(endpoint)

    assert response.status_code == 200


def test_runtime_requirements_are_exactly_pinned():
    requirements = Path(__file__).resolve().parents[1] / "requirements.txt"
    lines = [line.strip() for line in requirements.read_text(encoding="utf-8").splitlines()]
    entries = [line for line in lines if line and not line.startswith("#")]

    assert entries
    assert all("==" in line for line in entries)


def test_dockerfile_runs_as_non_root_and_keeps_healthcheck_local():
    dockerfile = (Path(__file__).resolve().parents[1] / "Dockerfile").read_text(encoding="utf-8")

    assert "useradd --system" in dockerfile
    assert "USER app" in dockerfile
    assert "http://127.0.0.1:8080/health" in dockerfile


def test_active_http_surface_excludes_legacy_memory_summary_task():
    response = TestClient(app).post("/tasks/memory-summary", json={"lead_id": "lead-1"})

    assert response.status_code == 404


def test_cors_allows_wear_control_put_requests():
    settings = _base_settings(CORS_ALLOWED_ORIGINS="http://localhost:3000")
    cors_app = __import__("src.main", fromlist=["build_app"]).build_app(settings)

    response = TestClient(cors_app).options(
        "/api/jobs/job-1/wear-controls",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "PUT",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "PUT" in response.headers["access-control-allow-methods"]
