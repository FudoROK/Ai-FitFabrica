"""FastAPI routes for backend-owned product-card workflows."""

from __future__ import annotations

import base64
import binascii
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from src.entrypoints.runtime_dependencies import operations_runtime_dependencies, product_card_runtime_dependencies
from src.settings import Settings
from src.use_cases.product_card.workflow_service import ProductCardSourceFile
from src.domain.product_card import ProductCardRequest

router = APIRouter()


class ProductCardSourceFilePayload(BaseModel):
    """Typed JSON payload for one source file sent to the product-card route."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    payload_base64: str = Field(min_length=1)

    def to_source_file(self) -> ProductCardSourceFile:
        """Decode the payload and convert it into a workflow source-file object."""
        try:
            payload = base64.b64decode(self.payload_base64)
        except (ValueError, binascii.Error) as exc:
            raise HTTPException(status_code=422, detail="invalid_product_card_file_payload") from exc
        return ProductCardSourceFile(
            filename=self.filename,
            content_type=self.content_type,
            payload=payload,
        )


class ProductCardCreatePayload(BaseModel):
    """Typed create-job payload for backend-owned product-card routes."""

    model_config = ConfigDict(extra="forbid")

    title_hint: str | None = None
    target_channel: str = Field(min_length=1)
    brand_tone: str = Field(min_length=1)
    source_files: list[ProductCardSourceFilePayload] = Field(min_length=1)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


@router.post("/api/product-cards", status_code=202)
async def create_product_card(
    payload: ProductCardCreatePayload,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Create one backend-owned product-card job and enqueue background execution."""
    workflow_runtime = product_card_runtime_dependencies(settings)
    operations_runtime = operations_runtime_dependencies(settings)
    job = await workflow_runtime.workflow_service.create_product_card_job(
        request=ProductCardRequest(
            title_hint=payload.title_hint,
            target_channel=payload.target_channel,
            brand_tone=payload.brand_tone,
        ),
        source_files=[item.to_source_file() for item in payload.source_files],
    )
    await operations_runtime.dispatch_service.enqueue_workflow(
        workflow_type="product_card",
        workflow_reference=job.job_id,
        payload={"job_id": job.job_id},
        idempotency_key=f"product_card:{job.job_id}",
    )
    background_tasks.add_task(operations_runtime.worker_runtime.run_one_cycle)
    return job


@router.get("/api/product-cards/{job_id}")
async def get_product_card_job(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the current persisted state for one product-card job."""
    runtime = product_card_runtime_dependencies(settings)
    job = await runtime.workflow_service.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="product_card_job_not_found")
    return job


@router.get("/api/product-cards/{job_id}/result")
async def get_product_card_result(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the latest generated product-card result for one job."""
    runtime = product_card_runtime_dependencies(settings)
    version = await runtime.workflow_service.get_result(job_id)
    if version is None:
        raise HTTPException(status_code=404, detail="product_card_result_not_found")
    return version
