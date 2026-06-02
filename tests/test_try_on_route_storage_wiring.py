"""Route wiring tests for portable Try-On storage selection."""

from __future__ import annotations

from types import SimpleNamespace

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.storage.media_storage import TryOnMediaStorage
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.entrypoints import try_on_routes
from src.settings import Settings
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService


def _settings(**overrides: object) -> Settings:
    """Build minimal settings with explicit test defaults."""
    values: dict[str, object] = {
        "gcp_project_id": "test-project",
        "pubsub_topic_name": "agent-jobs",
    }
    values.update(overrides)
    return Settings(**values)


def test_default_try_on_service_uses_portable_in_memory_storage(monkeypatch) -> None:
    """Default route wiring must build Try-On storage from portable infrastructure."""
    object_storage = InMemoryObjectStorage()
    workflow_service = TryOnWorkflowService(
        repository=InMemoryTryOnJobRepository(),
        generator=FakeTryOnGenerationAdapter(),
        file_storage=TryOnMediaStorage(
            object_storage=object_storage,
            tenant_id="public",
            root_prefix="fitfabrica",
        ),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )
    monkeypatch.setattr(
        try_on_routes,
        "try_on_runtime_dependencies",
        lambda _settings: SimpleNamespace(
            job_repository=workflow_service._repository,
            file_storage=workflow_service._file_storage,
            generation_adapter=workflow_service._generator,
            workflow_service=workflow_service,
        ),
    )

    service = try_on_routes._service(_settings())

    assert isinstance(service._repository, InMemoryTryOnJobRepository)
    assert isinstance(service._file_storage, TryOnMediaStorage)
    assert service._file_storage._object_storage is object_storage


def test_try_on_service_uses_portable_s3_storage_when_enabled(monkeypatch) -> None:
    """Portable route wiring must route through runtime object storage regardless of provider."""
    fake_s3_storage = object()
    workflow_service = TryOnWorkflowService(
        repository=InMemoryTryOnJobRepository(),
        generator=FakeTryOnGenerationAdapter(),
        file_storage=TryOnMediaStorage(
            object_storage=fake_s3_storage,
            tenant_id="public",
            root_prefix="fitfabrica",
        ),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )
    monkeypatch.setattr(
        try_on_routes,
        "try_on_runtime_dependencies",
        lambda _settings: SimpleNamespace(
            job_repository=workflow_service._repository,
            file_storage=workflow_service._file_storage,
            generation_adapter=workflow_service._generator,
            workflow_service=workflow_service,
        ),
    )
    settings = _settings(
        OBJECT_STORAGE_BACKEND="s3",
        OBJECT_STORAGE_BUCKET_NAME="fitfabrica-media",
    )

    service = try_on_routes._service(settings)

    assert isinstance(service._file_storage, TryOnMediaStorage)
    assert service._file_storage._object_storage is fake_s3_storage
