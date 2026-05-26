"""Google Cloud Storage adapter for Try-On upload persistence."""
from __future__ import annotations

import re
from functools import partial
from typing import Protocol

from anyio import to_thread
from google.cloud import storage

from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.ports import TryOnFileStoragePort


class GcsBlob(Protocol):
    """Subset of a Cloud Storage blob used by this adapter."""

    name: str

    def upload_from_string(self, data: bytes, content_type: str) -> None:
        """Upload bytes to the object."""
        ...


class GcsBucket(Protocol):
    """Subset of a Cloud Storage bucket used by this adapter."""

    name: str

    def blob(self, name: str) -> GcsBlob:
        """Return a blob handle for an object name."""
        ...


class GcsTryOnFileStorage(TryOnFileStoragePort):
    """Persist Try-On uploads in Google Cloud Storage."""

    def __init__(self, bucket: GcsBucket, upload_prefix: str) -> None:
        """Create a GCS-backed upload storage adapter."""
        self._bucket = bucket
        self._upload_prefix = upload_prefix.strip("/")

    @classmethod
    def from_bucket_name(cls, bucket_name: str, upload_prefix: str) -> "GcsTryOnFileStorage":
        """Create the adapter from a configured bucket name."""
        client = storage.Client()
        return cls(bucket=client.bucket(bucket_name), upload_prefix=upload_prefix)

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
        """Upload bytes to GCS and return an internal gs:// reference."""
        object_name = self._object_name(job_id=job_id, role=role, filename=filename)
        blob = self._bucket.blob(object_name)
        upload = partial(blob.upload_from_string, payload, content_type=content_type)
        await to_thread.run_sync(upload)
        return TryOnStoredInput(
            role=role,
            storage_backend="gcs",
            uri=f"gs://{self._bucket.name}/{object_name}",
            bucket_name=self._bucket.name,
            object_name=object_name,
            content_type=content_type,
            size_bytes=len(payload),
            sha256=sha256_hex,
        )

    def _object_name(self, *, job_id: str, role: TryOnUploadRole, filename: str) -> str:
        """Build a stable object path without exposing raw unsafe filename characters."""
        safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-") or role.value
        return f"{self._upload_prefix}/{job_id}/{role.value}/{safe_filename}"
