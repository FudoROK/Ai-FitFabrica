"""Settings tests for portable Try-On storage selection."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.settings import Settings


def _settings(**overrides: object) -> Settings:
    """Build minimal settings with explicit test defaults."""
    values: dict[str, object] = {
        "GCP_PROJECT_ID": "test-project",
        "PUBSUB_TOPIC_NAME": "agent-jobs",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_try_on_storage_defaults_to_portable_in_memory_and_repository_settings() -> None:
    """Local settings must stay on portable in-memory object storage by default."""
    settings = _settings()

    assert settings.try_on_job_repository_backend == "in_memory"
    assert settings.try_on_generation_backend == "sandbox_fake"
    assert settings.object_storage_backend == "in_memory"
    assert settings.object_storage_prefix == "fitfabrica"
    assert settings.try_on_firestore_collection == "try_on_jobs"


def test_vertex_virtual_try_on_requires_vertex_project(monkeypatch: pytest.MonkeyPatch) -> None:
    """Real Vertex Try-On backend must not boot without a configured Vertex project."""
    monkeypatch.delenv("VERTEX_PROJECT", raising=False)
    with pytest.raises(ValidationError, match="vertex_project"):
        _settings(
            TRY_ON_GENERATION_BACKEND="vertex_virtual_try_on",
            ENABLE_REAL_TRY_ON_GENERATION=True,
            VERTEX_PROJECT="",
        )


def test_vertex_virtual_try_on_requires_explicit_real_activation_flag() -> None:
    """The real Vertex Try-On path must stay disabled until rollout is explicitly approved."""
    with pytest.raises(ValidationError, match="enable_real_try_on_generation"):
        _settings(
            TRY_ON_GENERATION_BACKEND="vertex_virtual_try_on",
            VERTEX_PROJECT="fitfabrica-test",
        )


def test_real_try_on_activation_requires_durable_storage_queue_and_database() -> None:
    """Real Vertex Try-On activation must require durable persistence and worker transport."""
    with pytest.raises(ValidationError, match="object_storage_backend"):
        _settings(
            TRY_ON_GENERATION_BACKEND="vertex_virtual_try_on",
            ENABLE_REAL_TRY_ON_GENERATION=True,
            VERTEX_PROJECT="fitfabrica-test",
        )


def test_real_try_on_activation_accepts_durable_rollout_settings() -> None:
    """Explicit rollout config should validate when all durable runtime prerequisites are present."""
    settings = _settings(
        TRY_ON_GENERATION_BACKEND="vertex_virtual_try_on",
        ENABLE_REAL_TRY_ON_GENERATION=True,
        VERTEX_PROJECT="fitfabrica-test",
        OBJECT_STORAGE_BACKEND="s3",
        OBJECT_STORAGE_BUCKET_NAME="fitfabrica-prod",
        POSTGRES_DSN="postgresql+asyncpg://fitfabrica:fitfabrica@localhost:5432/fitfabrica",
        OPERATIONS_QUEUE_BACKEND="redis",
        REDIS_URL="redis://localhost:6379/0",
    )

    assert settings.enable_real_try_on_generation is True
    assert settings.try_on_generation_backend == "vertex_virtual_try_on"


def test_real_try_on_production_fallback_requires_unsafe_override() -> None:
    """Production-like environments must not silently keep a fallback backend for real Vertex rollout."""
    settings = _settings(
        ENVIRONMENT="production",
        TRY_ON_GENERATION_BACKEND="vertex_virtual_try_on",
        ENABLE_REAL_TRY_ON_GENERATION=True,
        VERTEX_PROJECT="fitfabrica-test",
        OBJECT_STORAGE_BACKEND="s3",
        OBJECT_STORAGE_BUCKET_NAME="fitfabrica-prod",
        POSTGRES_DSN="postgresql+asyncpg://fitfabrica:fitfabrica@localhost:5432/fitfabrica",
        OPERATIONS_QUEUE_BACKEND="redis",
        REDIS_URL="redis://localhost:6379/0",
        TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND="provider_runtime",
    )

    from src.settings import validate_settings

    with pytest.raises(ValueError, match="TRY_ON_VERTEX_FAILURE_FALLBACK_BACKEND"):
        validate_settings(settings)


def test_portable_s3_storage_requires_bucket_name() -> None:
    """Selecting the portable S3 backend without a bucket must fail."""
    with pytest.raises(ValidationError, match="object_storage_bucket_name"):
        _settings(OBJECT_STORAGE_BACKEND="s3")


def test_firestore_repository_requires_collection_name() -> None:
    """Selecting Firestore without a collection must fail during settings validation."""
    with pytest.raises(ValidationError, match="try_on_firestore_collection"):
        _settings(
            try_on_job_repository_backend="firestore",
            try_on_firestore_collection="   ",
        )
