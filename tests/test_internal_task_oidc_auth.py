from datetime import date

from fastapi.testclient import TestClient
import pytest

from src.main import app
from src.memory_layer.services.memory_summary_service import MemorySummaryResult
from src.settings import Settings, validate_settings


client = TestClient(app)


def _base_settings(**overrides) -> Settings:
    payload = {
        "_env_file": None,
        "GCP_PROJECT_ID": "test-project",
        "PUBSUB_TOPIC_NAME": "test-topic",
        "VERTEX_PROJECT": "test-project",
        "VERTEX_AGENT_RESOURCE": "test-agent",
        "HUBSPOT_ACCESS_TOKEN": "test-hubspot-token",
        "ENVIRONMENT": "test",
        "memory_summary_enabled": False,
    }
    payload.update(overrides)
    return Settings(**payload)


def _mock_oidc_verifier(monkeypatch):
    def _verify(token: str, _request, audience: str):
        tokens = {
            "memory-ok": {
                "aud": "https://tasks.example.test/memory-summary",
                "email": "memory-task@test-project.iam.gserviceaccount.com",
                "iss": "https://accounts.google.com",
                "email_verified": True,
            },
            "wrong-caller": {
                "aud": "https://tasks.example.test/memory-summary",
                "email": "other@test-project.iam.gserviceaccount.com",
                "iss": "https://accounts.google.com",
                "email_verified": True,
            },
            "wrong-issuer": {
                "aud": "https://tasks.example.test/memory-summary",
                "email": "memory-task@test-project.iam.gserviceaccount.com",
                "iss": "https://issuer.example.com",
                "email_verified": True,
            },
        }
        claims = tokens.get(token)
        if not claims:
            raise ValueError("invalid token")
        if claims["aud"] != audience:
            raise ValueError("wrong audience")
        return claims

    monkeypatch.setattr("google.oauth2.id_token.verify_oauth2_token", _verify)



def test_memory_summary_missing_bearer_rejected_and_runtime_not_called(monkeypatch):
    called = {"runtime": False}

    class _Svc:
        async def build_memory_summary_for_lead(self, **_kwargs):
            called["runtime"] = True
            return MemorySummaryResult(date=date(2026, 3, 19), leads_processed=1, summaries_written=1, errors=[])

    monkeypatch.setattr("src.entrypoints.internal_task_routes.memory_summary_service", lambda _settings=None: _Svc())

    response = client.post("/tasks/memory-summary", json={"lead_id": "lead-1"})

    assert response.status_code == 401
    assert called["runtime"] is False



def test_internal_task_malformed_bearer_rejected(monkeypatch):
    _mock_oidc_verifier(monkeypatch)

    response = client.post(
        "/tasks/memory-summary",
        headers={"Authorization": "Bearer not-a-valid-token"},
        json={"lead_id": "lead-1"},
    )

    assert response.status_code == 401


def test_internal_task_wrong_caller_rejected(monkeypatch):
    _mock_oidc_verifier(monkeypatch)

    response = client.post(
        "/tasks/memory-summary",
        headers={"Authorization": "Bearer wrong-caller"},
        json={"lead_id": "lead-1"},
    )

    assert response.status_code == 401


def test_internal_task_wrong_audience_rejected(monkeypatch):
    _mock_oidc_verifier(monkeypatch)

    response = client.post(
        "/tasks/memory-summary",
        headers={"Authorization": "Bearer daily-ok"},
        json={"lead_id": "lead-1"},
    )

    assert response.status_code == 401


def test_internal_task_valid_oidc_accepted(monkeypatch):
    _mock_oidc_verifier(monkeypatch)

    class _Svc:
        async def build_memory_summary_for_lead(self, **_kwargs):
            return MemorySummaryResult(date=date(2026, 3, 19), leads_processed=1, summaries_written=1, errors=[])

    monkeypatch.setattr("src.entrypoints.internal_task_routes.memory_summary_service", lambda _settings=None: _Svc())

    response = client.post(
        "/tasks/memory-summary",
        headers={"Authorization": "Bearer memory-ok"},
        json={"lead_id": "lead-1"},
    )

    assert response.status_code == 200
    assert response.json()["pipeline_status"] == "completed"



def test_x_auth_token_rejected_always(monkeypatch):
    called = {"runtime": False}

    class _Svc:
        async def build_memory_summary_for_lead(self, **_kwargs):
            called["runtime"] = True
            return MemorySummaryResult(date=date(2026, 3, 19), leads_processed=1, summaries_written=1, errors=[])

    monkeypatch.setattr("src.entrypoints.internal_task_routes.memory_summary_service", lambda _settings=None: _Svc())

    response = client.post(
        "/tasks/memory-summary",
        headers={"X-Auth-Token": "legacy-shared-secret"},
        json={"lead_id": "lead-1"},
    )

    assert response.status_code == 401
    assert called["runtime"] is False


def test_settings_validation_fails_without_required_internal_oidc_config():
    settings = _base_settings(
        memory_summary_enabled=True,
        memory_summary_task_auth_audience=None,
        memory_summary_task_allowed_service_accounts=[],
    )

    with pytest.raises(ValueError):
        validate_settings(settings)


def test_rate_limit_fail_mode_defaults_to_closed():
    settings = _base_settings()
    assert settings.rate_limit_fail_mode == "closed"


def test_settings_validation_blocks_fail_open_in_production():
    settings = _base_settings(
        ENVIRONMENT="prod",
        rate_limit_fail_mode="open",
    )

    with pytest.raises(ValueError, match="RATE_LIMIT_FAIL_MODE=open is not allowed"):
        validate_settings(settings)


def test_settings_validation_allows_fail_open_in_non_production():
    settings = _base_settings(ENVIRONMENT="test", rate_limit_fail_mode="open")
    validate_settings(settings)


def test_settings_validation_allows_explicit_prod_override_for_fail_open():
    settings = _base_settings(
        ENVIRONMENT="production",
        rate_limit_fail_mode="open",
        allow_unsafe_rate_limit_fail_open_in_production=True,
    )
    validate_settings(settings)
