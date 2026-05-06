import base64
import json

from fastapi.testclient import TestClient

from src.main import app
from src.settings import Settings


client = TestClient(app)


def _base_settings(**overrides) -> Settings:
    payload = {
        "_env_file": None,
        "telegram_bot_token": "test-token",
        "GCP_PROJECT_ID": "test-project",
        "PUBSUB_TOPIC_NAME": "test-topic",
        "VERTEX_PROJECT": "test-project",
        "VERTEX_AGENT_RESOURCE": "test-agent",
        "HUBSPOT_ACCESS_TOKEN": "test-hubspot-token",
        "ENVIRONMENT": "test",
        "memory_summary_enabled": False,
        "pubsub_push_audience": "https://pubsub.example.test/push",
        "pubsub_push_service_account_email": "pubsub-push@test-project.iam.gserviceaccount.com",
    }
    payload.update(overrides)
    return Settings(**payload)


def _pubsub_request_payload(data: dict) -> dict:
    encoded = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
    return {
        "message": {
            "data": encoded,
            "messageId": "msg-1",
            "publishTime": "2026-03-24T00:00:00Z",
        },
        "subscription": "projects/test/subscriptions/sub",
    }


def _mock_pubsub_oidc_verifier(monkeypatch):
    def _verify(token: str, _request, audience: str):
        tokens = {
            "pubsub-ok": {
                "aud": "https://pubsub.example.test/push",
                "email": "pubsub-push@test-project.iam.gserviceaccount.com",
                "iss": "https://accounts.google.com",
                "email_verified": True,
            },
            "pubsub-wrong-issuer": {
                "aud": "https://pubsub.example.test/push",
                "email": "pubsub-push@test-project.iam.gserviceaccount.com",
                "iss": "https://issuer.example.com",
                "email_verified": True,
            },
            "pubsub-wrong-email": {
                "aud": "https://pubsub.example.test/push",
                "email": "other@test-project.iam.gserviceaccount.com",
                "iss": "https://accounts.google.com",
                "email_verified": True,
            },
            "pubsub-unverified": {
                "aud": "https://pubsub.example.test/push",
                "email": "pubsub-push@test-project.iam.gserviceaccount.com",
                "iss": "https://accounts.google.com",
                "email_verified": False,
            },
        }
        claims = tokens.get(token)
        if not claims:
            raise ValueError("invalid token")
        if claims["aud"] != audience:
            raise ValueError("wrong audience")
        return claims

    monkeypatch.setattr("src.entrypoints.policies.id_token.verify_oauth2_token", _verify)


def test_pubsub_valid_oidc_accepted(monkeypatch):
    app.state.settings = _base_settings()
    _mock_pubsub_oidc_verifier(monkeypatch)

    called = {"runtime": False}

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(*_args, **_kwargs):
        called["runtime"] = True
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)

    response = client.post(
        "/pubsub",
        headers={"Authorization": "Bearer pubsub-ok"},
        json=_pubsub_request_payload(
            {
                "channel": "telegram",
                "source_identity": "1",
                "event_identity": "evt-1",
                "conversation_identity": "conv-1",
                "text": "hi",
            }
        ),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert called["runtime"] is True


def test_pubsub_wrong_issuer_rejected_and_runtime_not_called(monkeypatch):
    app.state.settings = _base_settings()
    _mock_pubsub_oidc_verifier(monkeypatch)

    called = {"runtime": False}

    async def _process(*_args, **_kwargs):
        called["runtime"] = True
        raise AssertionError("runtime should not be called for unauthorized request")

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)

    response = client.post(
        "/pubsub",
        headers={"Authorization": "Bearer pubsub-wrong-issuer"},
        json=_pubsub_request_payload(
            {
                "channel": "telegram",
                "source_identity": "1",
                "event_identity": "evt-1",
                "conversation_identity": "conv-1",
                "text": "hi",
            }
        ),
    )

    assert response.status_code == 401
    assert called["runtime"] is False


def test_pubsub_existing_email_check_still_enforced(monkeypatch):
    app.state.settings = _base_settings()
    _mock_pubsub_oidc_verifier(monkeypatch)

    response = client.post(
        "/pubsub",
        headers={"Authorization": "Bearer pubsub-wrong-email"},
        json=_pubsub_request_payload(
            {
                "channel": "telegram",
                "source_identity": "1",
                "event_identity": "evt-1",
                "conversation_identity": "conv-1",
                "text": "hi",
            }
        ),
    )

    assert response.status_code == 401


def test_pubsub_existing_email_verified_check_still_enforced(monkeypatch):
    app.state.settings = _base_settings()
    _mock_pubsub_oidc_verifier(monkeypatch)

    response = client.post(
        "/pubsub",
        headers={"Authorization": "Bearer pubsub-unverified"},
        json=_pubsub_request_payload(
            {
                "channel": "telegram",
                "source_identity": "1",
                "event_identity": "evt-1",
                "conversation_identity": "conv-1",
                "text": "hi",
            }
        ),
    )

    assert response.status_code == 401
