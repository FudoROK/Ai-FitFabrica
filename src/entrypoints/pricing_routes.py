"""FastAPI routes for backend-owned pricing workflows."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from src.domain.pricing import PricingRequest
from src.entrypoints.runtime_dependencies import operations_runtime_dependencies, pricing_runtime_dependencies
from src.settings import Settings

router = APIRouter()


class PricingCreatePayload(BaseModel):
    """Typed create-job payload for backend-owned pricing routes."""

    model_config = ConfigDict(extra="forbid")

    product_id: str = Field(min_length=1)
    target_currency: str = Field(min_length=1)
    desired_margin_percent: float | None = Field(default=None, ge=0)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


@router.post("/api/pricing-jobs", status_code=202)
async def create_pricing_job(
    payload: PricingCreatePayload,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Create one backend-owned pricing job and enqueue background execution."""
    workflow_runtime = pricing_runtime_dependencies(settings)
    operations_runtime = operations_runtime_dependencies(settings)
    job = await workflow_runtime.workflow_service.create_pricing_job(
        request=PricingRequest(
            product_id=payload.product_id,
            target_currency=payload.target_currency,
            desired_margin_percent=payload.desired_margin_percent,
        )
    )
    await operations_runtime.dispatch_service.enqueue_workflow(
        workflow_type="pricing",
        workflow_reference=job.job_id,
        payload={"job_id": job.job_id},
        idempotency_key=f"pricing:{job.job_id}",
    )
    background_tasks.add_task(operations_runtime.worker_runtime.run_one_cycle)
    return job


@router.get("/api/pricing-jobs/{job_id}")
async def get_pricing_job(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the current persisted state for one pricing job."""
    runtime = pricing_runtime_dependencies(settings)
    job = await runtime.workflow_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="pricing_job_not_found")
    return job


@router.get("/api/pricing-jobs/{job_id}/result")
async def get_pricing_result(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the latest persisted pricing recommendation for one job."""
    runtime = pricing_runtime_dependencies(settings)
    recommendation = await runtime.workflow_service.get_result(job_id)
    if recommendation is None:
        raise HTTPException(status_code=404, detail="pricing_result_not_found")
    return recommendation
