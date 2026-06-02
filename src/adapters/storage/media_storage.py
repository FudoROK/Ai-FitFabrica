"""Workflow-facing adapters built on portable object storage."""

from __future__ import annotations

from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.ports import TryOnFileStoragePort

from .contracts import ObjectStorage
from .object_naming import build_media_object_key


class TryOnMediaStorage(TryOnFileStoragePort):
    """Persist Try-On uploads through the portable object storage contract."""

    def __init__(self, *, object_storage: ObjectStorage, tenant_id: str, root_prefix: str) -> None:
        """Bind object storage plus naming scope for Try-On uploads."""
        self._object_storage = object_storage
        self._tenant_id = tenant_id
        self._root_prefix = root_prefix

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
        """Persist upload bytes and return a portable stored-input reference."""
        object_key = build_media_object_key(
            tenant_id=self._tenant_id,
            workflow="try-on",
            job_id=job_id,
            role=role.value,
            filename=filename,
            root_prefix=self._root_prefix,
        )
        stored = self._object_storage.put_bytes(
            object_key=object_key,
            payload=payload,
            content_type=content_type,
        )
        if stored.storage_backend == "in_memory":
            uri = f"memory://{stored.object_key}"
        else:
            bucket_name = stored.bucket_name or "unknown-bucket"
            uri = f"{stored.storage_backend}://{bucket_name}/{stored.object_key}"
        return TryOnStoredInput(
            role=role,
            storage_backend=stored.storage_backend,
            uri=uri,
            bucket_name=stored.bucket_name,
            object_key=stored.object_key,
            object_name=stored.object_key,
            content_type=content_type,
            size_bytes=len(payload),
            sha256=sha256_hex,
        )
