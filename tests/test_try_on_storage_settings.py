"""Settings tests for Try-On storage adapter selection."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.settings import Settings


def _settings(**overrides: object) -> Settings:
    """Build minimal settings with explicit test defaults."""
    values: dict[str, object] = {
        "gcp_project_id": "test-project",
        "pubsub_topic_name": "agent-jobs",
        "telegram_bot_token": "token",
    }
    values.update(overrides)
    return Settings(**values)


def test_try_on_storage_defaults_to_in_memory_adapters() -> None:
    """Local settings must not opt into cloud-backed Try-On storage."""
    settings = _settings()

    assert settings.try_on_file_storage_backend == "in_memory"
    assert settings.try_on_job_repository_backend == "in_memory"
    assert settings.try_on_gcs_bucket_name is None
    assert settings.try_on_gcs_upload_prefix == "try-on/uploads"
    assert settings.try_on_firestore_collection == "try_on_jobs"


def test_gcs_storage_requires_bucket_name() -> None:
    """Selecting GCS without a bucket must fail during settings validation."""
    with pytest.raises(ValidationError, match="try_on_gcs_bucket_name"):
        _settings(try_on_file_storage_backend="gcs")


def test_firestore_repository_requires_collection_name() -> None:
    """Selecting Firestore without a collection must fail during settings validation."""
    with pytest.raises(ValidationError, match="try_on_firestore_collection"):
        _settings(
            try_on_job_repository_backend="firestore",
            try_on_firestore_collection="   ",
        )
