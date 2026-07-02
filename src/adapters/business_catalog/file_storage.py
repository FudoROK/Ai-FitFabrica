"""Object-storage adapter for business catalog product media."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.adapters.storage.contracts import ObjectStorage
from src.adapters.storage.object_naming import build_media_object_key


@dataclass(frozen=True)
class BusinessCatalogObjectStorage:
    """Persist B2B catalog uploads through the portable object-storage contract."""

    object_storage: ObjectStorage
    tenant_id: str
    root_prefix: str

    async def save_upload(self, *, owner_id: str, filename: str, content_type: str, content: bytes) -> str:
        """Store one catalog upload and return the object key."""

        upload_digest = hashlib.sha256(content).hexdigest()[:16]
        object_key = build_media_object_key(
            tenant_id=self.tenant_id,
            workflow="business-catalog",
            job_id=owner_id,
            role=f"upload-{upload_digest}",
            filename=filename,
            root_prefix=self.root_prefix,
        )
        stored = self.object_storage.put_bytes(
            object_key=object_key,
            payload=content,
            content_type=content_type,
        )
        return stored.object_key
