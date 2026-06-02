"""Tests for portable Try-On media storage."""

from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import UploadFile

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.storage.media_storage import TryOnMediaStorage
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import TryOnJobStatus, TryOnUploadRole
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService


@pytest.mark.asyncio
async def test_try_on_media_storage_persists_upload_with_portable_reference() -> None:
    """Portable media storage must emit backend-owned object references."""
    object_storage = InMemoryObjectStorage()
    storage = TryOnMediaStorage(
        object_storage=object_storage,
        tenant_id="public",
        root_prefix="fitfabrica",
    )

    stored = await storage.save_upload(
        job_id="job-1",
        role=TryOnUploadRole.HUMAN_PHOTO,
        filename="human photo.jpg",
        content_type="image/jpeg",
        payload=b"image-bytes",
        sha256_hex="a" * 64,
    )

    assert stored.storage_backend == "in_memory"
    assert stored.object_key == "fitfabrica/tenants/public/try-on/job-1/human_photo/human-photo.jpg"
    assert stored.object_name == stored.object_key
    assert stored.uri == "memory://fitfabrica/tenants/public/try-on/job-1/human_photo/human-photo.jpg"


def _upload(filename: str, content_type: str, payload: bytes) -> UploadFile:
    """Build an UploadFile for workflow tests."""
    return UploadFile(file=BytesIO(payload), filename=filename, headers={"content-type": content_type})


@pytest.mark.asyncio
async def test_try_on_workflow_service_accepts_portable_media_storage() -> None:
    """Workflow service must persist stored inputs through the portable media adapter."""
    repository = InMemoryTryOnJobRepository()
    storage = TryOnMediaStorage(
        object_storage=InMemoryObjectStorage(),
        tenant_id="public",
        root_prefix="fitfabrica",
    )
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        file_storage=storage,
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg"},
            max_upload_bytes=1024,
        ),
    )

    job = await service.create_job(
        human_photo=_upload("human.jpg", "image/jpeg", b"human-photo"),
        garment_photo=_upload("garment.jpg", "image/jpeg", b"garment-photo"),
    )

    assert job.status == TryOnJobStatus.ACCEPTED
    assert [stored.role for stored in job.stored_inputs] == [
        TryOnUploadRole.HUMAN_PHOTO,
        TryOnUploadRole.GARMENT_PHOTO,
    ]
    assert all(stored.object_key is not None for stored in job.stored_inputs)
    assert all(stored.uri.startswith("memory://fitfabrica/tenants/public/try-on/") for stored in job.stored_inputs)
