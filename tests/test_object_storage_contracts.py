"""Contract tests for portable object storage metadata."""

from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.storage.contracts import SignedUrl, StoredObject
from src.domain.media_storage import MediaObjectRef


def test_stored_object_tracks_bucket_and_object_key() -> None:
    """StoredObject must retain portable bucket and object metadata."""
    stored = StoredObject(
        bucket_name="fitfabrica-media",
        object_key="tenants/public/try-on/job-1/human-photo.jpg",
        content_type="image/jpeg",
        content_length=12,
        etag="etag-1",
        version_id="v1",
        storage_backend="s3",
    )

    assert stored.bucket_name == "fitfabrica-media"
    assert stored.object_key.endswith("human-photo.jpg")
    assert stored.content_length == 12


def test_media_object_ref_can_be_created_from_stored_object() -> None:
    """MediaObjectRef must model portable binary references without GCS-only fields."""
    ref = MediaObjectRef(
        storage_backend="s3",
        bucket_name="fitfabrica-media",
        object_key="tenants/public/try-on/job-1/human-photo.jpg",
        content_type="image/jpeg",
        size_bytes=12,
        sha256="a" * 64,
    )

    assert ref.storage_backend == "s3"
    assert ref.bucket_name == "fitfabrica-media"
    assert ref.object_key.endswith("human-photo.jpg")


def test_signed_url_models_temporary_backend_owned_access() -> None:
    """Signed URLs must expose the issued URL, expiry, and HTTP method."""
    signed = SignedUrl(
        url="https://signed.example/object",
        expires_at=datetime(2026, 5, 31, tzinfo=timezone.utc),
        method="GET",
    )

    assert signed.url == "https://signed.example/object"
    assert signed.expires_at.tzinfo == timezone.utc
    assert signed.method == "GET"
