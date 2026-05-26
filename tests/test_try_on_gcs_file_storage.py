"""Tests for the Try-On GCS file storage adapter using local fakes."""
from __future__ import annotations

import pytest

from src.adapters.try_on.gcs_file_storage import GcsTryOnFileStorage
from src.domain.try_on import TryOnUploadRole


class FakeBlob:
    """Minimal fake Cloud Storage blob."""

    def __init__(self, name: str) -> None:
        """Create a fake blob with no uploaded payload."""
        self.name = name
        self.uploaded_payload: bytes | None = None
        self.uploaded_content_type: str | None = None

    def upload_from_string(self, data: bytes, content_type: str) -> None:
        """Capture the uploaded bytes and content type."""
        self.uploaded_payload = data
        self.uploaded_content_type = content_type


class FakeBucket:
    """Minimal fake Cloud Storage bucket."""

    def __init__(self, name: str) -> None:
        """Create a fake bucket."""
        self.name = name
        self.blobs: dict[str, FakeBlob] = {}

    def blob(self, name: str) -> FakeBlob:
        """Return a fake blob by object name."""
        blob = FakeBlob(name)
        self.blobs[name] = blob
        return blob


@pytest.mark.asyncio
async def test_gcs_file_storage_builds_prefixed_object_reference() -> None:
    """GCS adapter must upload bytes and return a non-public gs:// reference."""
    bucket = FakeBucket("fitfabrica-test-bucket")
    storage = GcsTryOnFileStorage(bucket=bucket, upload_prefix="try-on/uploads")

    stored = await storage.save_upload(
        job_id="try_on_123",
        role=TryOnUploadRole.HUMAN_PHOTO,
        filename="human photo.jpg",
        content_type="image/jpeg",
        payload=b"image-bytes",
        sha256_hex="a" * 64,
    )

    assert stored.storage_backend == "gcs"
    assert stored.bucket_name == "fitfabrica-test-bucket"
    assert stored.object_name == "try-on/uploads/try_on_123/human_photo/human-photo.jpg"
    assert stored.uri == "gs://fitfabrica-test-bucket/try-on/uploads/try_on_123/human_photo/human-photo.jpg"
    assert bucket.blobs[stored.object_name].uploaded_payload == b"image-bytes"
    assert bucket.blobs[stored.object_name].uploaded_content_type == "image/jpeg"
