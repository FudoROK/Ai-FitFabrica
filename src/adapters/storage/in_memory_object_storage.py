"""In-memory object storage adapter for tests and local bootstrap."""

from __future__ import annotations

from datetime import timedelta

from src.domain.try_on import utc_now

from .contracts import SignedUrl, StoredObject


class InMemoryObjectStorage:
    """Simple in-process object storage implementation."""

    def __init__(self) -> None:
        """Initialize the in-memory object registry."""
        self._objects: dict[str, tuple[bytes, str]] = {}

    def put_bytes(self, *, object_key: str, payload: bytes, content_type: str) -> StoredObject:
        """Store bytes under a deterministic key and return storage metadata."""
        self._objects[object_key] = (payload, content_type)
        return StoredObject(
            bucket_name=None,
            object_key=object_key,
            content_type=content_type,
            content_length=len(payload),
            etag=None,
            version_id=None,
            storage_backend="in_memory",
        )

    def get_bytes(self, object_key: str) -> bytes:
        """Return previously stored bytes or fail fast for unknown keys."""
        payload, _content_type = self._objects[object_key]
        return payload

    def create_signed_get_url(self, object_key: str, *, expires_in_seconds: int) -> SignedUrl:
        """Return a deterministic in-memory URL for tests and local diagnostics."""
        return SignedUrl(
            url=f"memory://{object_key}",
            expires_at=utc_now() + timedelta(seconds=expires_in_seconds),
            method="GET",
        )
