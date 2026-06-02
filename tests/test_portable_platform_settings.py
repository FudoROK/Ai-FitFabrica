from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.settings import Settings, validate_settings


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "GCP_PROJECT_ID": "test-project",
        "PUBSUB_TOPIC_NAME": "agent-jobs",
        "MEMORY_SUMMARY_ENABLED": False,
    }
    values.update(overrides)
    return Settings(**values)


def test_portable_backends_default_to_postgres_redis_s3_qdrant_ready_settings() -> None:
    settings = _settings()

    assert settings.rate_limit_backend == "redis"
    assert settings.object_storage_backend == "in_memory"
    assert settings.vector_backend == "qdrant"
    assert settings.postgres_dsn is None


def test_s3_backend_requires_bucket_name() -> None:
    with pytest.raises(ValidationError, match="object_storage_bucket_name"):
        _settings(OBJECT_STORAGE_BACKEND="s3")


def test_qdrant_backend_rejects_blank_url_when_overridden() -> None:
    with pytest.raises(ValidationError, match="qdrant_url"):
        _settings(QDRANT_URL="   ")


def test_postgres_settings_accept_database_url_alias() -> None:
    settings = _settings(DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/fitfabrica")

    assert settings.postgres_dsn == "postgresql+asyncpg://user:pass@localhost:5432/fitfabrica"


def test_portable_settings_accept_generic_project_and_event_aliases() -> None:
    settings = Settings(
        PROJECT_ID="portable-project",
        EVENT_TOPIC_NAME="portable-events",
        MEMORY_SUMMARY_ENABLED=False,
    )

    assert settings.gcp_project_id == "portable-project"
    assert settings.pubsub_topic_name == "portable-events"


def test_messaging_provider_is_web_first_only() -> None:
    settings = _settings(MESSAGING_PROVIDER="none")

    assert settings.messaging_provider == "none"
    validate_settings(settings)

    with pytest.raises(ValueError, match="MESSAGING_PROVIDER"):
        validate_settings(
            Settings(
                GCP_PROJECT_ID="test-project",
                PUBSUB_TOPIC_NAME="agent-jobs",
                MEMORY_SUMMARY_ENABLED=False,
                MESSAGING_PROVIDER="telegram",
            )
        )


def test_object_storage_signed_url_ttl_defaults_to_15_minutes() -> None:
    settings = _settings()

    assert settings.object_storage_signed_url_ttl_seconds == 900
