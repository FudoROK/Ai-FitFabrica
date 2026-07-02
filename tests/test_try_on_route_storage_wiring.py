"""Route wiring tests for portable Try-On storage selection."""

from __future__ import annotations

from types import SimpleNamespace
import asyncio

from fastapi.testclient import TestClient

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.storage.object_naming import build_media_object_key
from src.adapters.storage.media_storage import TryOnMediaStorage
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnJob,
    TryOnJobStatus,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStatusEvent,
    TryOnUploadRole,
)
from src.entrypoints import try_on_routes
from src.main import app
from src.settings import Settings
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from tests.try_on_analysis_bundle_stub import required_analysis_bundle
from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter
from tests.try_on_human_identity_stub import AllowingHumanIdentityAnalysisStub


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
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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


def test_generated_try_on_result_uses_browser_safe_backend_artifact_url(monkeypatch) -> None:
    """Generated images must not expose internal MinIO hosts to browser clients."""
    object_storage = InMemoryObjectStorage()
    repository = InMemoryTryOnJobRepository()
    job_id = "try_on_public_artifact"
    object_key = build_media_object_key(
        tenant_id="public",
        workflow="try-on",
        job_id=job_id,
        role="result_image",
        filename="result.png",
        root_prefix="fitfabrica",
    )
    object_storage.put_bytes(object_key=object_key, payload=b"real-png-bytes", content_type="image/png")
    result_image = TryOnResultImage(
        kind="generated_artifact",
        url="http://minio:9000/fitfabrica-staging/fitfabrica/tenants/public/try-on/try_on_public_artifact/result_image/result.png",
        alt="Vertex Virtual Try-On result preview",
    )
    result_image._artifact_object_key = object_key
    job = TryOnJob(
        job_id=job_id,
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        status=TryOnJobStatus.COMPLETED,
        input_metadata=[
            TryOnInputMetadata(
                role=TryOnUploadRole.HUMAN_PHOTO,
                filename="human.png",
                content_type="image/png",
                size_bytes=10,
                sha256="a" * 64,
            )
        ],
        status_history=[TryOnStatusEvent(status=TryOnJobStatus.COMPLETED, stage="completed", message="done")],
        result=TryOnResult(
            job_id=job_id,
            result_image=result_image,
            quality_report=TryOnQualityReport(verdict="pass", confidence=0.9),
            stylist_note="done",
        ),
    )
    asyncio.run(repository.save(job))
    workflow_service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
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
            workflow_service=workflow_service,
            object_storage=object_storage,
            object_storage_root_prefix="fitfabrica",
        ),
    )
    client = TestClient(app)

    result_response = client.get(
        f"/api/jobs/{job_id}/result",
        headers={"x-forwarded-proto": "https", "host": "api.fit.aisoulfabrica.com"},
    )

    assert result_response.status_code == 200
    public_image = result_response.json()["result"]["result_image"]
    assert public_image["url"] == f"https://api.fit.aisoulfabrica.com/api/jobs/{job_id}/artifacts/result-image"
    assert "minio" not in str(public_image)
    artifact_response = client.get(public_image["url"])
    assert artifact_response.status_code == 200
    assert artifact_response.content == b"real-png-bytes"
    assert artifact_response.headers["content-type"] == "image/png"
