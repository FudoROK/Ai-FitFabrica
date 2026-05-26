"""FastAPI routes for the Try-On sandbox job lifecycle."""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.firestore_repository import FirestoreTryOnJobRepository
from src.adapters.try_on.gcs_file_storage import GcsTryOnFileStorage
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import (
    TryOnError,
    TryOnErrorCode,
    TryOnErrorResponse,
    TryOnJobCreatedResponse,
    TryOnJobStatus,
    TryOnJobStatusResponse,
    TryOnNotReadyResponse,
    TryOnResultResponse,
    TryOnSandboxLifecycleMode,
)
from src.settings import Settings
from src.use_cases.try_on.ports import TryOnFileStoragePort, TryOnJobRepositoryPort
from src.use_cases.try_on.storage_errors import TryOnStorageError
from src.use_cases.try_on.workflow_service import (
    TryOnUploadValidationConfig,
    TryOnValidationError,
    TryOnWorkflowService,
)

router = APIRouter()


@lru_cache(maxsize=1)
def _in_memory_repository() -> InMemoryTryOnJobRepository:
    """Return the process-local non-durable Try-On job repository."""
    return InMemoryTryOnJobRepository()


@lru_cache(maxsize=1)
def _in_memory_file_storage() -> InMemoryTryOnFileStorage:
    """Return the process-local non-durable Try-On file storage."""
    return InMemoryTryOnFileStorage()


@lru_cache(maxsize=8)
def _firestore_repository(collection_name: str) -> FirestoreTryOnJobRepository:
    """Return a cached Firestore repository for the configured collection."""
    return FirestoreTryOnJobRepository.from_collection_name(collection_name)


@lru_cache(maxsize=8)
def _gcs_file_storage(bucket_name: str, upload_prefix: str) -> GcsTryOnFileStorage:
    """Return a cached GCS file storage adapter for the configured bucket."""
    return GcsTryOnFileStorage.from_bucket_name(bucket_name=bucket_name, upload_prefix=upload_prefix)


def _repository(settings: Settings) -> TryOnJobRepositoryPort:
    """Select the Try-On job repository adapter from settings."""
    if settings.try_on_job_repository_backend == "firestore":
        return _firestore_repository(settings.try_on_firestore_collection)
    return _in_memory_repository()


def _file_storage(settings: Settings) -> TryOnFileStoragePort:
    """Select the Try-On file storage adapter from settings."""
    if settings.try_on_file_storage_backend == "gcs":
        if settings.try_on_gcs_bucket_name is None:
            raise RuntimeError("try_on_gcs_bucket_name is required for GCS Try-On storage")
        return _gcs_file_storage(
            bucket_name=settings.try_on_gcs_bucket_name,
            upload_prefix=settings.try_on_gcs_upload_prefix,
        )
    return _in_memory_file_storage()


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _service(settings: Settings) -> TryOnWorkflowService:
    """Create a Try-On workflow service using configured persistence adapters."""
    return TryOnWorkflowService(
        repository=_repository(settings),
        generator=FakeTryOnGenerationAdapter(),
        file_storage=_file_storage(settings),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types=set(settings.try_on_allowed_content_types),
            max_upload_bytes=settings.try_on_max_upload_bytes,
        ),
    )


def _error_response(status_code: int, error: TryOnError) -> JSONResponse:
    """Return a typed Try-On error response with a controlled status code."""
    body = TryOnErrorResponse(error=error)
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


def _job_not_found_error(job_id: str) -> TryOnError:
    """Build the canonical not-found error for missing jobs."""
    return TryOnError(
        code=TryOnErrorCode.JOB_NOT_FOUND,
        message="Try-On job was not found.",
        details={"job_id": job_id},
    )


@router.post("/api/try-on/jobs", status_code=201, response_model=None)
async def create_try_on_job(
    settings: Annotated[Settings, Depends(_settings)],
    human_photo: Annotated[UploadFile | None, File()] = None,
    garment_photo: Annotated[UploadFile | None, File()] = None,
    sandbox_lifecycle_mode: Annotated[
        TryOnSandboxLifecycleMode,
        Form(description="Sandbox-only lifecycle mode for exercising async clients."),
    ] = TryOnSandboxLifecycleMode.COMPLETE,
) -> TryOnJobCreatedResponse | JSONResponse:
    """Create and complete a sandbox Try-On job from two uploaded images."""
    try:
        job = await _service(settings).create_job(
            human_photo=human_photo,
            garment_photo=garment_photo,
            lifecycle_mode=sandbox_lifecycle_mode,
        )
    except TryOnValidationError as exc:
        return _error_response(422, exc.error)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())

    return TryOnJobCreatedResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        status=job.status,
        input_metadata=job.input_metadata,
        status_url=f"/api/jobs/{job.job_id}/status",
        result_url=f"/api/jobs/{job.job_id}/result",
    )


@router.get("/api/jobs/{job_id}/status", response_model=None)
async def get_try_on_job_status(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
) -> TryOnJobStatusResponse | JSONResponse:
    """Return the status history and sandbox cost events for a Try-On job."""
    try:
        job = await _service(settings).get_job(job_id)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
    if job is None:
        return _error_response(404, _job_not_found_error(job_id))

    return TryOnJobStatusResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        status=job.status,
        status_history=job.status_history,
        cost_events=job.cost_events,
    )


@router.get("/api/jobs/{job_id}/result", response_model=None)
async def get_try_on_job_result(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
) -> TryOnResultResponse | TryOnNotReadyResponse | JSONResponse:
    """Return a completed Try-On result or a typed lifecycle response."""
    try:
        job = await _service(settings).get_job(job_id)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
    if job is None:
        return _error_response(404, _job_not_found_error(job_id))
    if job.status == TryOnJobStatus.FAILED:
        return _error_response(
            409,
            TryOnError(
                code=TryOnErrorCode.JOB_FAILED,
                message="Try-On job failed.",
                details={"job_id": job.job_id},
            ),
        )
    if job.status != TryOnJobStatus.COMPLETED or job.result is None:
        body = TryOnNotReadyResponse(
            status="not_ready",
            job_id=job.job_id,
            workflow_type=job.workflow_type,
            current_status=job.status,
            status_url=f"/api/jobs/{job.job_id}/status",
        )
        return JSONResponse(status_code=202, content=body.model_dump(mode="json"))

    return TryOnResultResponse(
        status="completed",
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        result=job.result,
    )
