"""Workspace read-only garment taxonomy API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from src.domain.garment_taxonomy import GarmentWearControl, GarmentWearControlRiskLevel
from src.entrypoints.runtime_dependencies import garment_taxonomy_service
from src.settings import Settings

router = APIRouter(prefix="/api/garment-taxonomy", tags=["garment-taxonomy"])


class GarmentWearControlResponse(BaseModel):
    """One approved user-facing way-of-wearing option."""

    model_config = ConfigDict(extra="forbid")

    control_code: str
    display_name: str
    description: str | None
    instruction_template: str
    risk_level: GarmentWearControlRiskLevel
    default_for_auto: bool


class GarmentWearControlListResponse(BaseModel):
    """Approved wear controls for one garment type."""

    model_config = ConfigDict(extra="forbid")

    garment_type: str = Field(min_length=1)
    taxonomy_item_code: str | None
    controls: list[GarmentWearControlResponse]
    created_candidate: bool = False


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _service_or_error(settings: Settings):
    service = garment_taxonomy_service(settings)
    if service is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "garment_taxonomy_storage_unavailable",
                    "message": "Garment taxonomy storage is not configured.",
                }
            },
        )
    return service


def _serialize_control(control: GarmentWearControl) -> GarmentWearControlResponse:
    """Convert one domain wear-control into the public API shape."""
    return GarmentWearControlResponse(
        control_code=control.control_code,
        display_name=control.display_name,
        description=control.description,
        instruction_template=control.instruction_template,
        risk_level=control.risk_level,
        default_for_auto=control.default_for_auto,
    )


@router.get("/wear-controls", response_model=GarmentWearControlListResponse)
async def get_garment_wear_controls(
    settings: Annotated[Settings, Depends(_settings)],
    garment_type: Annotated[str, Query(min_length=1)],
) -> GarmentWearControlListResponse | JSONResponse:
    """Return backend-approved wear controls for a garment type."""
    service = _service_or_error(settings)
    if isinstance(service, JSONResponse):
        return service

    result = await service.resolve_available_controls(garment_type=garment_type)
    return GarmentWearControlListResponse(
        garment_type=garment_type,
        taxonomy_item_code=result.taxonomy_item.code if result.taxonomy_item else None,
        controls=[_serialize_control(control) for control in result.available_controls],
        created_candidate=result.created_candidate is not None,
    )
