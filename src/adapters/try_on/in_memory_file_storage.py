"""In-memory Try-On file storage adapter for local development and tests."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.ports import TryOnFileStoragePort


@dataclass(frozen=True)
class StoredUploadPayload:
    """In-memory payload retained for tests and local sandbox behavior."""

    content_type: str
    payload: bytes


class InMemoryTryOnFileStorage(TryOnFileStoragePort):
    """Process-local file storage adapter that never touches external services."""

    def __init__(self) -> None:
        """Create an empty in-memory upload store."""
        self._uploads: dict[str, StoredUploadPayload] = {}
        self._lock = asyncio.Lock()

    async def save_upload(
        self,
        *,
        job_id: str,
        role: TryOnUploadRole,
        filename: str,
        content_type: str,
        payload: bytes,
        sha256_hex: str,
    ) -> TryOnStoredInput:
        """Persist upload bytes in process memory and return a stable memory URI."""
        object_name = f"{job_id}/{role.value}/{filename}"
        uri = f"memory://try-on/{object_name}"
        async with self._lock:
            self._uploads[uri] = StoredUploadPayload(content_type=content_type, payload=payload)
        return TryOnStoredInput(
            role=role,
            storage_backend="in_memory",
            uri=uri,
            object_name=object_name,
            content_type=content_type,
            size_bytes=len(payload),
            sha256=sha256_hex,
        )

    async def get_payload(self, uri: str) -> StoredUploadPayload | None:
        """Return a stored payload for tests and local diagnostics."""
        async with self._lock:
            return self._uploads.get(uri)
