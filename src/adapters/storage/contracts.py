"""Neutral object storage contracts for binary artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol


@dataclass(frozen=True)
class SignedUrl:
    """Temporary backend-issued URL for reading a stored object."""

    url: str
    expires_at: datetime
    method: Literal["GET"]


@dataclass(frozen=True)
class StoredObject:
    """Metadata returned after storing a binary object."""

    bucket_name: str | None
    object_key: str
    content_type: str
    content_length: int
    etag: str | None
    version_id: str | None
    storage_backend: str


class ObjectStorage(Protocol):
    """Storage contract used by workflow adapters and services."""

    def put_bytes(self, *, object_key: str, payload: bytes, content_type: str) -> StoredObject:
        """Persist bytes under the given object key and return storage metadata."""

    def get_bytes(self, object_key: str) -> bytes:
        """Read the stored bytes for a backend-owned object key."""

    def create_signed_get_url(self, object_key: str, *, expires_in_seconds: int) -> SignedUrl:
        """Return a temporary backend-issued GET URL for a stored object."""
