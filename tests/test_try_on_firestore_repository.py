"""Tests for Firestore Try-On repository serialization using local fakes."""
from __future__ import annotations

import pytest

from src.adapters.try_on.firestore_repository import FirestoreTryOnJobRepository
from src.domain.try_on import TryOnJob, TryOnJobStatus, TryOnStoredInput, TryOnUploadRole


class FakeSnapshot:
    """Minimal Firestore document snapshot fake."""

    def __init__(self, exists: bool, data: dict[str, object] | None) -> None:
        """Create a fake snapshot."""
        self.exists = exists
        self._data = data

    def to_dict(self) -> dict[str, object] | None:
        """Return fake document data."""
        return self._data


class FakeDocument:
    """Minimal Firestore document fake."""

    def __init__(self) -> None:
        """Create an empty fake document."""
        self.data: dict[str, object] | None = None

    def set(self, data: dict[str, object]) -> None:
        """Persist fake document data."""
        self.data = data

    def get(self) -> FakeSnapshot:
        """Return a fake snapshot for the current document."""
        return FakeSnapshot(exists=self.data is not None, data=self.data)


class FakeCollection:
    """Minimal Firestore collection fake."""

    def __init__(self) -> None:
        """Create an empty fake collection."""
        self.documents: dict[str, FakeDocument] = {}

    def document(self, document_id: str) -> FakeDocument:
        """Return a fake document by ID."""
        if document_id not in self.documents:
            self.documents[document_id] = FakeDocument()
        return self.documents[document_id]


@pytest.mark.asyncio
async def test_firestore_repository_round_trips_try_on_job() -> None:
    """Firestore repository must serialize and parse strict Try-On job models."""
    collection = FakeCollection()
    repository = FirestoreTryOnJobRepository(collection=collection)
    job = TryOnJob(
        job_id="try_on_123",
        status=TryOnJobStatus.GENERATING,
        stored_inputs=[
            TryOnStoredInput(
                role=TryOnUploadRole.HUMAN_PHOTO,
                storage_backend="gcs",
                uri="gs://bucket/key",
                bucket_name="bucket",
                object_name="key",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            )
        ],
    )

    await repository.save(job)
    loaded = await repository.get("try_on_123")

    assert loaded == job


@pytest.mark.asyncio
async def test_firestore_repository_returns_none_for_missing_job() -> None:
    """Missing Firestore documents must map to None."""
    repository = FirestoreTryOnJobRepository(collection=FakeCollection())

    assert await repository.get("missing") is None
