"""Tests for typed Try-On storage failure handling."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.adapters.try_on.firestore_repository import FirestoreTryOnJobRepository
from src.adapters.try_on.gcs_file_storage import GcsTryOnFileStorage
from src.domain.try_on import TryOnErrorCode
from src.domain.try_on import TryOnJob, TryOnJobStatus, TryOnUploadRole
from src.main import app
from src.use_cases.try_on import storage_errors
from src.use_cases.try_on.storage_errors import TryOnStorageError


client = TestClient(app)


def test_try_on_storage_error_builds_public_safe_details() -> None:
    """Storage errors must expose backend/operation without leaking provider internals."""
    error = TryOnStorageError(
        backend="gcs",
        operation="save_upload",
        public_message="Try-On storage is temporarily unavailable.",
    )

    assert error.backend == "gcs"
    assert error.operation == "save_upload"
    assert error.public_message == "Try-On storage is temporarily unavailable."
    assert error.to_try_on_error().code == TryOnErrorCode.STORAGE_UNAVAILABLE
    assert error.to_try_on_error().details == {
        "backend": "gcs",
        "operation": "save_upload",
    }


class FailingGcsBlob:
    """Fake blob that raises during upload."""

    name = "try-on/uploads/job/human_photo/file.jpg"

    def upload_from_string(self, data: bytes, content_type: str) -> None:
        """Raise like a provider SDK failure without requiring live GCS."""
        raise RuntimeError("provider credential failure with internal details")


class FailingGcsBucket:
    """Fake bucket that returns a failing blob."""

    name = "fitfabrica-test-bucket"

    def blob(self, name: str) -> FailingGcsBlob:
        """Return a failing blob."""
        return FailingGcsBlob()


@pytest.mark.asyncio
async def test_gcs_adapter_wraps_provider_failures() -> None:
    """GCS provider failures must become public-safe TryOnStorageError exceptions."""
    storage = GcsTryOnFileStorage(bucket=FailingGcsBucket(), upload_prefix="try-on/uploads")

    with pytest.raises(TryOnStorageError) as exc_info:
        await storage.save_upload(
            job_id="try_on_123",
            role=TryOnUploadRole.HUMAN_PHOTO,
            filename="human.jpg",
            content_type="image/jpeg",
            payload=b"image",
            sha256_hex="a" * 64,
        )

    assert exc_info.value.backend == "gcs"
    assert exc_info.value.operation == "save_upload"
    assert "credential" not in exc_info.value.public_message.lower()


class FailingFirestoreDocument:
    """Fake document that raises during reads and writes."""

    def set(self, data: dict[str, object]) -> None:
        """Raise during save."""
        raise RuntimeError("firestore permission denied internal details")

    def get(self) -> object:
        """Raise during read."""
        raise RuntimeError("firestore deadline exceeded internal details")


class FailingFirestoreCollection:
    """Fake collection returning a failing document."""

    def document(self, document_id: str) -> FailingFirestoreDocument:
        """Return a failing document."""
        return FailingFirestoreDocument()


@pytest.mark.asyncio
async def test_firestore_repository_wraps_save_failures() -> None:
    """Firestore save failures must become public-safe TryOnStorageError exceptions."""
    repository = FirestoreTryOnJobRepository(collection=FailingFirestoreCollection())
    job = TryOnJob(job_id="try_on_123", status=TryOnJobStatus.GENERATING)

    with pytest.raises(TryOnStorageError) as exc_info:
        await repository.save(job)

    assert exc_info.value.backend == "firestore"
    assert exc_info.value.operation == "save_job"
    assert "permission" not in exc_info.value.public_message.lower()


@pytest.mark.asyncio
async def test_firestore_repository_wraps_get_failures() -> None:
    """Firestore read failures must become public-safe TryOnStorageError exceptions."""
    repository = FirestoreTryOnJobRepository(collection=FailingFirestoreCollection())

    with pytest.raises(TryOnStorageError) as exc_info:
        await repository.get("try_on_123")

    assert exc_info.value.backend == "firestore"
    assert exc_info.value.operation == "get_job"
    assert "deadline" not in exc_info.value.public_message.lower()


class RaisingWorkflowService:
    """Service fake that raises storage failures from every public operation."""

    async def create_job(self, *args: object, **kwargs: object) -> object:
        """Raise a storage failure while creating a job."""
        raise storage_errors.TryOnStorageError(
            backend="gcs",
            operation="save_upload",
            public_message="Try-On upload storage is temporarily unavailable.",
        )

    async def get_job(self, job_id: str) -> object:
        """Raise a storage failure while reading a job."""
        raise storage_errors.TryOnStorageError(
            backend="firestore",
            operation="get_job",
            public_message="Try-On job storage is temporarily unavailable.",
        )


def test_create_job_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST must return a typed 503 instead of an unstructured server error."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.jpg", b"human-image", "image/jpeg"),
            "garment_photo": ("garment.jpg", b"garment-image", "image/jpeg"),
        },
    )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "storage_unavailable",
        "message": "Try-On upload storage is temporarily unavailable.",
        "details": {"backend": "gcs", "operation": "save_upload"},
    }


def test_status_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Status polling must return a typed 503 for storage read failures."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.get("/api/jobs/try_on_123/status")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"
    assert response.json()["error"]["details"] == {"backend": "firestore", "operation": "get_job"}


def test_result_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Result polling must return a typed 503 for storage read failures."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.get("/api/jobs/try_on_123/result")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"
    assert response.json()["error"]["details"] == {"backend": "firestore", "operation": "get_job"}
