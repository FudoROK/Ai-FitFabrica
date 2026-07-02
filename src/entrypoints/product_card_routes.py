"""FastAPI routes for backend-owned product-card workflows."""

from __future__ import annotations

import base64
import binascii
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.billing import BillingOwnerType
from src.domain.product_card import ProductCardRequest
from src.entrypoints.runtime_dependencies import (
    billing_runtime_dependencies,
    operations_runtime_dependencies,
    product_card_runtime_dependencies,
    workspace_capability_service,
)
from src.settings import Settings
from src.use_cases.product_card.workflow_service import ProductCardSourceFile
from src.use_cases.workspace.capability_service import WorkspaceCapabilityDeniedError

router = APIRouter()
_ALLOWED_PRODUCT_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_PRODUCT_IMAGE_BYTES = 10 * 1024 * 1024


class ProductCardSourceFilePayload(BaseModel):
    """Typed JSON payload for one source file sent to the product-card route."""

    model_config = ConfigDict(extra="forbid")

    filename: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    payload_base64: str = Field(min_length=1)

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        """Reject source files that are not supported product images."""
        if value not in _ALLOWED_PRODUCT_IMAGE_TYPES:
            raise ValueError("unsupported_product_card_image_type")
        return value

    def to_source_file(self) -> ProductCardSourceFile:
        """Decode the payload and convert it into a workflow source-file object."""
        try:
            payload = base64.b64decode(self.payload_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise HTTPException(status_code=422, detail="invalid_product_card_file_payload") from exc
        if not payload:
            raise HTTPException(status_code=422, detail="empty_product_card_file_payload")
        if len(payload) > _MAX_PRODUCT_IMAGE_BYTES:
            raise HTTPException(status_code=422, detail="product_card_file_too_large")
        return ProductCardSourceFile(
            filename=self.filename,
            content_type=self.content_type,
            payload=payload,
        )


class ProductCardCreatePayload(BaseModel):
    """Typed create-job payload for backend-owned product-card routes."""

    model_config = ConfigDict(extra="forbid")

    title_hint: str = Field(min_length=1)
    category: str = Field(min_length=1)
    target_channel: str = Field(min_length=1)
    brand_tone: str = Field(min_length=1)
    source_files: list[ProductCardSourceFilePayload] = Field(min_length=1)


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _owner_id(settings: Settings) -> str:
    """Return the unified workspace owner used by Product Card capability checks."""
    return getattr(settings, "default_person_credit_account_id", "public-person")


async def _require_product_card_capability(settings: Settings) -> JSONResponse | None:
    """Return a structured denial when Product Card creation is unavailable."""
    try:
        await workspace_capability_service(settings).require_capability(
            owner_id=_owner_id(settings),
            capability="product_card_create",
        )
    except WorkspaceCapabilityDeniedError as error:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "workspace_capability_denied",
                    "message": error.reason,
                    "details": {"capability": error.capability},
                }
            },
        )
    return None


async def _require_product_card_credits(settings: Settings) -> JSONResponse | None:
    """Return a structured denial before creating a job with insufficient credits."""
    if not bool(getattr(settings, "billing_core_enabled", False)):
        return None
    required_credits = int(getattr(settings, "product_card_base_credit_cost", 18))
    balance = await billing_runtime_dependencies(settings).billing_service.get_account_balance(
        owner_id=_owner_id(settings),
        owner_type=BillingOwnerType.PERSON,
    )
    if balance.available_credits >= required_credits:
        return None
    return JSONResponse(
        status_code=402,
        content={
            "error": {
                "code": "insufficient_credits",
                "message": "Недостаточно кредитов для создания карточки товара.",
                "details": {
                    "available_credits": balance.available_credits,
                    "required_credits": required_credits,
                },
            }
        },
    )


@router.post("/api/product-cards", status_code=202, response_model=None)
async def create_product_card(
    payload: ProductCardCreatePayload,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Create one backend-owned product-card job and enqueue background execution."""
    denied = await _require_product_card_capability(settings)
    if denied is not None:
        return denied
    credit_denied = await _require_product_card_credits(settings)
    if credit_denied is not None:
        return credit_denied
    workflow_runtime = product_card_runtime_dependencies(settings)
    operations_runtime = operations_runtime_dependencies(settings)
    job = await workflow_runtime.workflow_service.create_product_card_job(
        request=ProductCardRequest(
            title_hint=payload.title_hint,
            category=payload.category,
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


@router.get("/api/product-cards/{job_id}/garment-analysis")
async def get_product_card_garment_analysis(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
):
    """Return the validated persisted Garment Identity analysis for one job."""
    runtime = product_card_runtime_dependencies(settings)
    analysis = await runtime.workflow_service.get_garment_analysis(job_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="product_card_garment_analysis_not_found")
    return analysis
