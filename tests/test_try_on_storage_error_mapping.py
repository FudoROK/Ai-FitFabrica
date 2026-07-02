"""Tests for typed Try-On storage failure handling."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.domain.try_on import TryOnErrorCode
from src.main import app
from src.use_cases.try_on import storage_errors
from src.use_cases.try_on.storage_errors import TryOnStorageError


client = TestClient(app)


def test_try_on_storage_error_builds_public_safe_details() -> None:
    """Storage errors must expose backend/operation without leaking provider internals."""
    error = TryOnStorageError(
        backend="s3",
        operation="save_upload",
        public_message="Try-On storage is temporarily unavailable.",
    )

    assert error.backend == "s3"
    assert error.operation == "save_upload"
    assert error.public_message == "Try-On storage is temporarily unavailable."
    assert error.to_try_on_error().code == TryOnErrorCode.STORAGE_UNAVAILABLE
    assert error.to_try_on_error().details == {
        "backend": "s3",
        "operation": "save_upload",
    }


class RaisingWorkflowService:
    """Service fake that raises storage failures from every public operation."""

    async def create_job(self, *args: object, **kwargs: object) -> object:
        """Raise a storage failure while creating a job."""
        raise storage_errors.TryOnStorageError(
            backend="s3",
            operation="save_upload",
            public_message="Try-On upload storage is temporarily unavailable.",
        )

    async def get_job(self, job_id: str) -> object:
        """Raise a storage failure while reading a job."""
        raise storage_errors.TryOnStorageError(
            backend="sql",
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
        "details": {"backend": "s3", "operation": "save_upload"},
    }


def test_status_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Status polling must return a typed 503 for storage read failures."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.get("/api/jobs/try_on_123/status")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"
    assert response.json()["error"]["details"] == {"backend": "sql", "operation": "get_job"}


def test_result_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Result polling must return a typed 503 for storage read failures."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.get("/api/jobs/try_on_123/result")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"
    assert response.json()["error"]["details"] == {"backend": "sql", "operation": "get_job"}
