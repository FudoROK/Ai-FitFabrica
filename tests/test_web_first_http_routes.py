from __future__ import annotations

from fastapi.testclient import TestClient

from src.main import build_app
from src.settings import Settings


def _web_first_settings() -> Settings:
    return Settings(
        ENVIRONMENT="test",
        GCP_PROJECT_ID="fitfabrica-test",
        PUBSUB_TOPIC_NAME="fitfabrica-events",
        LLM_PROVIDER="fake",
        MEMORY_SUMMARY_ENABLED=False,
        MESSAGING_PROVIDER="none",
    )


def test_web_first_app_does_not_mount_legacy_ingress_routes_by_default() -> None:
    client = TestClient(build_app(_web_first_settings()))

    assert client.post("/webhook/telegram", json={}).status_code == 404
    assert client.post("/pubsub", json={}).status_code == 404
