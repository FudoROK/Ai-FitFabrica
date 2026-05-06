import json
import logging
from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

import src.services.pubsub.pubsub_service as pubsub_service
import google.cloud.pubsub_v1 as pubsub_v1
from src.domain.normalized_ingress_event import NormalizedIngressEvent
from src.main import app
from src.services.rate_limit.contracts import RateLimitDecision, RateLimiter
from google.api_core.exceptions import GoogleAPIError

# Initialize TestClient for the FastAPI app
client = TestClient(app)

# Helper for creating a basic Telegram webhook payload
def _telegram_webhook_payload(update_id: int, chat_id: int, text: str) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": update_id,
            "date": 1710000000,
            "from": {"id": chat_id, "first_name": "John", "is_bot": False, "language_code": "en"},
            "chat": {"id": chat_id, "type": "private", "first_name": "John"},
            "text": text,
        },
    }

# Mock for normalize_telegram_update
def _mock_normalize_telegram_update(update: Any) -> NormalizedIngressEvent:
    message = update.message or update.edited_message
    chat_id = message.chat.id if message else "unknown"
    return NormalizedIngressEvent(
        channel="telegram",
        source_identity=str(chat_id),
        event_identity=str(update.update_id),
        conversation_identity=str(chat_id),
        external_user_id=str(chat_id),
        text=message.text,
        timestamp="2026-03-20T00:00:00+00:00",
        content_type="text",
    )

@pytest.fixture(autouse=True)
def common_monkeypatch_fixtures(monkeypatch):
    mocks = {}

    # Mock has_valid_token to always return True by default
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)
    # Mock normalize_telegram_update
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.normalize_telegram_update", _mock_normalize_telegram_update)

    # Mock publish_normalized_update
    mock_publish = MagicMock(return_value="mock-message-id")
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", mock_publish)
    mocks["publish_normalized_update"] = mock_publish

    # Mock Pub/Sub PublisherClient to prevent real network calls
    mock_publisher_client = MagicMock()
    mock_publisher_client.topic_path.return_value = "projects/test-project/topics/test-topic"
    mock_publisher_client.publish.return_value.result.return_value = "mock-message-id"
    monkeypatch.setattr("google.cloud.pubsub_v1.PublisherClient", MagicMock(return_value=mock_publisher_client))
    mocks["publisher_client"] = mock_publisher_client

    # Always allow global safety limiter by default unless specifically overridden
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_global_safety_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )

    yield mocks

def test_telegram_webhook_allowed_by_rate_limiter_succeeds(common_monkeypatch_fixtures, monkeypatch):
    # Mock ingress_rate_limiter to always allow
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_rate_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )

    response = client.post("/webhook/telegram", json=_telegram_webhook_payload(1, 101, "test message"))

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert common_monkeypatch_fixtures["publish_normalized_update"].called

def test_telegram_webhook_denied_by_rate_limiter_returns_429(common_monkeypatch_fixtures, monkeypatch):
    # Mock ingress_rate_limiter to deny
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_rate_limiter",
        lambda _settings: type(
            "DenyAll",
            (),
            {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="denied_limit_exceeded", remaining=0, retry_after_seconds=60, reason="test_limit_exceeded")},
        )(),
    )

    response = client.post("/webhook/telegram", json=_telegram_webhook_payload(2, 102, "test message"))

    assert response.status_code == 429
    assert response.json()["status"] == "rate_limited"
    assert response.json()["reason"] == "ingress_source_rate_limit_exceeded"
    assert not common_monkeypatch_fixtures["publish_normalized_update"].called

def test_telegram_webhook_rate_limiter_backend_error_fails_open(common_monkeypatch_fixtures, monkeypatch, caplog):
    # Mock ingress_rate_limiter to raise GoogleAPIError, wrapped by FailModeRateLimiter
    from src.services.rate_limit.factory import FailModeRateLimiter # Import inside test to avoid circular dep

    class MockErrorRateLimiter(RateLimiter):
        def allow(self, key: str) -> RateLimitDecision:
            raise GoogleAPIError("Mock Firestore error")

    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_rate_limiter",
        lambda _settings: FailModeRateLimiter(limiter=MockErrorRateLimiter(), fail_mode="open"),
    )

    with caplog.at_level(logging.ERROR):
        response = client.post("/webhook/telegram", json=_telegram_webhook_payload(3, 103, "test message"))

    assert response.status_code == 200 # Should fail-open
    assert response.json()["status"] == "queued" # Should still queue event
    assert common_monkeypatch_fixtures["publish_normalized_update"].called

    assert "RATE_LIMIT_BACKEND_FAILURE" in caplog.text

def test_telegram_webhook_global_limiter_denied_returns_429(common_monkeypatch_fixtures, monkeypatch):
    # Mock ingress_rate_limiter to allow
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_rate_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )
    # Mock ingress_global_safety_limiter to deny
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_global_safety_limiter",
        lambda _settings: type(
            "DenyAllGlobal",
            (),
            {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="denied_limit_exceeded", remaining=0, retry_after_seconds=30, reason="global_limit_exceeded")},
        )(),
    )

    response = client.post("/webhook/telegram", json=_telegram_webhook_payload(4, 104, "test message"))

    assert response.status_code == 429
    assert response.json()["status"] == "rate_limited"
    assert response.json()["reason"] == "ingress_global_safety_cap_exceeded"
    assert not common_monkeypatch_fixtures["publish_normalized_update"].called

def test_telegram_webhook_global_limiter_backend_error_fails_open(common_monkeypatch_fixtures, monkeypatch, caplog):
    # Mock ingress_rate_limiter to allow
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_rate_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )
    # Mock ingress_global_safety_limiter to raise GoogleAPIError, wrapped by FailModeRateLimiter
    from src.services.rate_limit.factory import FailModeRateLimiter # Import inside test to avoid circular dep

    class MockErrorGlobalLimiter(RateLimiter):
        def allow(self, key: str) -> RateLimitDecision:
            raise GoogleAPIError("Mock Global Firestore error")

    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_global_safety_limiter",
        lambda _settings: FailModeRateLimiter(limiter=MockErrorGlobalLimiter(), fail_mode="open"),
    )

    with caplog.at_level(logging.ERROR):
        response = client.post("/webhook/telegram", json=_telegram_webhook_payload(5, 105, "test message"))

    assert response.status_code == 200 # Should fail-open
    assert response.json()["status"] == "queued" # Should still queue event
    assert common_monkeypatch_fixtures["publish_normalized_update"].called

    assert "RATE_LIMIT_BACKEND_FAILURE" in caplog.text

def test_telegram_webhook_invalid_secret_token_is_rejected(common_monkeypatch_fixtures, monkeypatch):
    # Override has_valid_token to return False
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: False)

    response = client.post("/webhook/telegram", json=_telegram_webhook_payload(6, 106, "test message"))

    assert response.status_code == 401
    assert response.json()["error"] == "unauthorized"
    assert not common_monkeypatch_fixtures["publish_normalized_update"].called
