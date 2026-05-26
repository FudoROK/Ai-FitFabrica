"""Workflow tests for persisted Try-On upload references."""
from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import UploadFile

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import TryOnJobStatus, TryOnUploadRole
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService


def _upload(filename: str, content_type: str, payload: bytes) -> UploadFile:
    """Build an UploadFile suitable for direct use-case tests."""
    return UploadFile(file=BytesIO(payload), filename=filename, headers={"content-type": content_type})


@pytest.mark.asyncio
async def test_create_job_persists_validated_uploads_before_saving_job() -> None:
    """Try-On jobs must retain backend storage references for both uploaded inputs."""
    repository = InMemoryTryOnJobRepository()
    storage = InMemoryTryOnFileStorage()
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

    assert job.status == TryOnJobStatus.COMPLETED
    assert [stored.role for stored in job.stored_inputs] == [
        TryOnUploadRole.HUMAN_PHOTO,
        TryOnUploadRole.GARMENT_PHOTO,
    ]
    assert all(stored.storage_backend == "in_memory" for stored in job.stored_inputs)
    assert all(stored.uri.startswith("memory://try-on/") for stored in job.stored_inputs)
    assert await repository.get(job.job_id) == job
