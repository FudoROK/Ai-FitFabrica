"""Route wiring tests for Try-On storage adapter selection."""
from __future__ import annotations

import pytest

from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.entrypoints import try_on_routes
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


def test_default_try_on_service_uses_in_memory_storage() -> None:
    """Default route wiring must stay local and non-durable."""
    service = try_on_routes._service(_settings())

    assert isinstance(service._repository, InMemoryTryOnJobRepository)
    assert isinstance(service._file_storage, InMemoryTryOnFileStorage)


def test_google_try_on_adapters_are_selected_and_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    """Google adapter wiring must use cached factories without live clients in tests."""
    repository = InMemoryTryOnJobRepository()
    file_storage = InMemoryTryOnFileStorage()
    repository_calls: list[str] = []
    storage_calls: list[tuple[str, str]] = []

    def fake_firestore_repository(collection_name: str) -> InMemoryTryOnJobRepository:
        """Capture Firestore factory calls without creating a Google client."""
        repository_calls.append(collection_name)
        return repository

    def fake_gcs_file_storage(bucket_name: str, upload_prefix: str) -> InMemoryTryOnFileStorage:
        """Capture GCS factory calls without creating a Google client."""
        storage_calls.append((bucket_name, upload_prefix))
        return file_storage

    try_on_routes._firestore_repository.cache_clear()
    try_on_routes._gcs_file_storage.cache_clear()
    monkeypatch.setattr(
        try_on_routes.FirestoreTryOnJobRepository,
        "from_collection_name",
        fake_firestore_repository,
    )
    monkeypatch.setattr(try_on_routes.GcsTryOnFileStorage, "from_bucket_name", fake_gcs_file_storage)
    settings = _settings(
        try_on_job_repository_backend="firestore",
        try_on_file_storage_backend="gcs",
        try_on_gcs_bucket_name="fitfabrica-test-bucket",
    )

    first = try_on_routes._service(settings)
    second = try_on_routes._service(settings)

    assert first._repository is repository
    assert second._repository is repository
    assert first._file_storage is file_storage
    assert second._file_storage is file_storage
    assert repository_calls == ["try_on_jobs"]
    assert storage_calls == [("fitfabrica-test-bucket", "try-on/uploads")]
