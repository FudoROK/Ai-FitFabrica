"""FastAPI routes for the Try-On sandbox job lifecycle."""
from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
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
from src.use_cases.try_on.workflow_service import (
    TryOnUploadValidationConfig,
    TryOnValidationError,
    TryOnWorkflowService,
)

router = APIRouter()


@lru_cache(maxsize=1)
def _repository() -> InMemoryTryOnJobRepository:
    """Return the process-local non-durable Try-On job repository."""
    return InMemoryTryOnJobRepository()


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _service(settings: Settings) -> TryOnWorkflowService:
    """Create a Try-On workflow service using sandbox-only adapters."""
    return TryOnWorkflowService(
        repository=_repository(),
        generator=FakeTryOnGenerationAdapter(),
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
    job = await _service(settings).get_job(job_id)
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
    job = await _service(settings).get_job(job_id)
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
