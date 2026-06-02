"""Portable object-storage adapter for generated content-package artifacts."""

from __future__ import annotations

from dataclasses import dataclass

from src.adapters.storage.contracts import ObjectStorage
from src.adapters.storage.object_naming import build_media_object_key
from src.domain.content_package import ContentPackageOption
from src.use_cases.content_package.ports import ContentPackageArtifactStoragePort


@dataclass(frozen=True)
class ContentPackageArtifactStorage(ContentPackageArtifactStoragePort):
    """Persist generated content-package artifacts through the portable object-storage contract."""

    object_storage: ObjectStorage
    tenant_id: str
    root_prefix: str

    async def store_generated_assets(
        self,
        *,
        job_id: str,
        assets: list[ContentPackageOption],
    ) -> list[str]:
        """Persist generated package artifacts and return their object keys."""
        stored_keys: list[str] = []
        for index, asset in enumerate(assets):
            object_key = build_media_object_key(
                tenant_id=self.tenant_id,
                workflow="content-package",
                job_id=job_id,
                role=f"{asset.asset_kind}-{index}",
                filename=f"{asset.label}.txt",
                root_prefix=self.root_prefix,
            )
            stored = self.object_storage.put_bytes(
                object_key=object_key,
                payload=asset.label.encode("utf-8"),
                content_type="text/plain",
            )
            stored_keys.append(stored.object_key)
        return stored_keys
