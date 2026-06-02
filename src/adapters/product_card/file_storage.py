"""Workflow-facing file storage adapter for product-card source assets."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.adapters.storage.contracts import ObjectStorage
from src.adapters.storage.object_naming import build_media_object_key
from src.use_cases.product_card.ports import ProductCardFileStoragePort
from src.use_cases.product_card.workflow_service import ProductCardSourceFile


@dataclass(frozen=True)
class ProductCardObjectStorage:
    """Persist product-card source files through the portable object-storage contract."""

    object_storage: ObjectStorage
    tenant_id: str
    root_prefix: str

    async def store_many(self, *, source_files: list[ProductCardSourceFile]) -> list[str]:
        """Persist all incoming source files and return their stored object keys."""
        stored_keys: list[str] = []
        upload_batch_id = hashlib.sha256(
            "|".join(source.filename for source in source_files).encode("utf-8")
        ).hexdigest()[:16]
        for index, source in enumerate(source_files):
            object_key = build_media_object_key(
                tenant_id=self.tenant_id,
                workflow="product-card",
                job_id=upload_batch_id,
                role=f"source-{index}",
                filename=source.filename,
                root_prefix=self.root_prefix,
            )
            stored = self.object_storage.put_bytes(
                object_key=object_key,
                payload=source.payload,
                content_type=source.content_type,
            )
            stored_keys.append(stored.object_key)
        return stored_keys
