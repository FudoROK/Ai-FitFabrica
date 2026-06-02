"""FastAPI routes for backend-owned content-package workflows."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from src.domain.content_package import ContentPackageRequest
from src.entrypoints.runtime_dependencies import content_package_runtime_dependencies, operations_runtime_dependencies
from src.settings import Settings

router = APIRouter()


class ContentPackageCreatePayload(BaseModel):
    """Typed create-job payload for backend-owned content-package routes."""

    model_config = ConfigDict(extra="forbid")

    product_card_version_id: str = Field(min_length=1)
    package_name: str = Field(min_length=1)
    requested_channels: list[str] = Field(default_factory=list)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


@router.post("/api/content-packages", status_code=202)
async def create_content_package(
    payload: ContentPackageCreatePayload,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Create one backend-owned content-package job and enqueue background execution."""
    workflow_runtime = content_package_runtime_dependencies(settings)
    operations_runtime = operations_runtime_dependencies(settings)
    job = await workflow_runtime.workflow_service.create_content_package_job(
        request=ContentPackageRequest(
            product_card_version_id=payload.product_card_version_id,
            package_name=payload.package_name,
            requested_channels=list(payload.requested_channels),
        )
    )
    await operations_runtime.dispatch_service.enqueue_workflow(
        workflow_type="content_package",
        workflow_reference=job.job_id,
        payload={"job_id": job.job_id},
        idempotency_key=f"content_package:{job.job_id}",
    )
    background_tasks.add_task(operations_runtime.worker_runtime.run_one_cycle)
    return job


@router.get("/api/content-packages/{job_id}")
async def get_content_package_job(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the current persisted state for one content-package job."""
    runtime = content_package_runtime_dependencies(settings)
    job = await runtime.workflow_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="content_package_job_not_found")
    return job


@router.get("/api/content-packages/{job_id}/result")
async def get_content_package_result(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the latest generated content-package result for one job."""
    runtime = content_package_runtime_dependencies(settings)
    version = await runtime.workflow_service.get_result(job_id)
    if version is None:
        raise HTTPException(status_code=404, detail="content_package_result_not_found")
    return version
