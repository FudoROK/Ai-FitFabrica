"""FastAPI routes for the backend-owned Try-On sandbox lifecycle."""
from __future__ import annotations

from typing import Annotated

from urllib.parse import urlparse

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, ConfigDict, Field

from src.domain.garment_taxonomy import GarmentWearControl
from src.domain.try_on import (
    TryOnError,
    TryOnErrorCode,
    TryOnErrorResponse,
    TryOnJobCreatedResponse,
    TryOnJobStatus,
    TryOnJobStatusResponse,
    TryOnNotReadyResponse,
    TryOnResult,
    TryOnResultImage,
    TryOnResultResponse,
    TryOnSandboxLifecycleMode,
    TryOnWearControlSelection,
)
from src.adapters.storage.object_naming import build_media_object_key
from src.settings import Settings
from src.entrypoints.runtime_dependencies import (
    garment_taxonomy_service,
    operations_runtime_dependencies,
    try_on_runtime_dependencies,
)
from src.entrypoints.garment_taxonomy_routes import GarmentWearControlResponse
from src.use_cases.try_on.storage_errors import TryOnStorageError
from src.use_cases.try_on.workflow_service import (
    TryOnValidationError,
    TryOnWorkflowService,
)

router = APIRouter()


class TryOnGarmentSlotWearControlOptions(BaseModel):
    """User-facing wear-control options for one analyzed garment slot."""

    model_config = ConfigDict(extra="forbid")

    slot_role: str = Field(min_length=1)
    garment_type: str = Field(min_length=1)
    taxonomy_item_code: str | None
    selected_control_code: str = "auto"
    controls: list[GarmentWearControlResponse] = Field(default_factory=list)


class TryOnPreGenerationAnalysisResponse(BaseModel):
    """Analysis snapshot returned before Try-On generation starts."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    workflow_type: str = "try_on"
    status: TryOnJobStatus
    slots: list[TryOnGarmentSlotWearControlOptions]
    generate_url: str = Field(min_length=1)


class TryOnWearControlSelectionPayload(BaseModel):
    """User-selected wear-control code for one analyzed garment slot."""

    model_config = ConfigDict(extra="forbid")

    slot_role: str = Field(min_length=1)
    selected_control_code: str = Field(min_length=1)


class TryOnWearControlSelectionRequest(BaseModel):
    """Wear-control selections submitted before generation starts."""

    model_config = ConfigDict(extra="forbid")

    selections: list[TryOnWearControlSelectionPayload] = Field(min_length=1)


class TryOnWearControlSelectionResponse(BaseModel):
    """Persisted backend-validated wear-control selections."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(min_length=1)
    status: TryOnJobStatus
    selections: list[TryOnWearControlSelection]


def _settings(request: Request) -> Settings:
    """Return application settings attached during FastAPI bootstrap."""
    return request.app.state.settings


def _service(settings: Settings) -> TryOnWorkflowService:
    """Create a Try-On workflow service using configured persistence adapters."""
    return try_on_runtime_dependencies(settings).workflow_service


def _runtime(settings: Settings):
    """Return the configured Try-On runtime bundle."""
    return try_on_runtime_dependencies(settings)


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


@router.post("/api/try-on/jobs", status_code=202, response_model=None)
async def create_try_on_job(
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(_settings)],
    human_photo: Annotated[UploadFile | None, File()] = None,
    garment_photo: Annotated[UploadFile | None, File()] = None,
    upper_garment_photo: Annotated[UploadFile | None, File()] = None,
    lower_garment_photo: Annotated[UploadFile | None, File()] = None,
    outerwear_garment_photo: Annotated[UploadFile | None, File()] = None,
    full_body_garment_photo: Annotated[UploadFile | None, File()] = None,
    sandbox_lifecycle_mode: Annotated[
        TryOnSandboxLifecycleMode,
        Form(description="Sandbox-only lifecycle mode for exercising async clients."),
    ] = TryOnSandboxLifecycleMode.COMPLETE,
) -> TryOnJobCreatedResponse | JSONResponse:
    """Create one Try-On job and enqueue worker execution when requested."""
    try:
        job = await _service(settings).create_job(
            human_photo=human_photo,
            garment_photo=garment_photo,
            upper_garment_photo=upper_garment_photo,
            lower_garment_photo=lower_garment_photo,
            outerwear_garment_photo=outerwear_garment_photo,
            full_body_garment_photo=full_body_garment_photo,
        )
    except TryOnValidationError as exc:
        return _error_response(422, exc.error)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())

    if sandbox_lifecycle_mode != TryOnSandboxLifecycleMode.PENDING:
        operations_runtime = operations_runtime_dependencies(settings)
        await operations_runtime.dispatch_service.enqueue_workflow(
            workflow_type="try_on",
            workflow_reference=job.job_id,
            payload={"job_id": job.job_id, "sandbox_lifecycle_mode": sandbox_lifecycle_mode.value},
            idempotency_key=f"try_on:{job.job_id}",
        )
        background_tasks.add_task(operations_runtime.worker_runtime.run_one_cycle)

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
    request: Request,
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
        if job.error is not None:
            return _error_response(409, job.error)
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
        result=_public_result(
            job_id=job.job_id,
            result=job.result,
            public_base_url=_public_base_url(request),
        ),
    )


@router.post("/api/jobs/{job_id}/generate", status_code=202, response_model=None)
async def continue_try_on_job_generation(
    job_id: str,
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(_settings)],
    sandbox_lifecycle_mode: Annotated[
        TryOnSandboxLifecycleMode,
        Form(description="Generation lifecycle mode after pre-generation analysis."),
    ] = TryOnSandboxLifecycleMode.COMPLETE,
) -> TryOnJobCreatedResponse | JSONResponse:
    """Continue one analysis-ready Try-On job into instruction and generation."""
    try:
        job = await _service(settings).get_job(job_id)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
    if job is None:
        return _error_response(404, _job_not_found_error(job_id))
    if job.status != TryOnJobStatus.ANALYSIS_READY:
        return _error_response(
            409,
            TryOnError(
                code=TryOnErrorCode.JOB_FAILED,
                message="Try-On job is not ready for generation continuation.",
                details={"job_id": job_id, "status": job.status.value},
            ),
        )
    if sandbox_lifecycle_mode == TryOnSandboxLifecycleMode.ANALYSIS_ONLY:
        return _error_response(
            422,
            TryOnError(
                code=TryOnErrorCode.JOB_FAILED,
                message="Generation continuation cannot use analysis_only mode.",
                details={"job_id": job_id},
            ),
        )

    operations_runtime = operations_runtime_dependencies(settings)
    await operations_runtime.dispatch_service.enqueue_workflow(
        workflow_type="try_on",
        workflow_reference=job.job_id,
        payload={"job_id": job.job_id, "sandbox_lifecycle_mode": sandbox_lifecycle_mode.value},
        idempotency_key=f"try_on:generate:{job.job_id}",
    )
    background_tasks.add_task(operations_runtime.worker_runtime.run_one_cycle)
    return TryOnJobCreatedResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        status=job.status,
        input_metadata=job.input_metadata,
        status_url=f"/api/jobs/{job.job_id}/status",
        result_url=f"/api/jobs/{job.job_id}/result",
    )


@router.put("/api/jobs/{job_id}/wear-controls", response_model=None)
async def save_try_on_wear_controls(
    job_id: str,
    payload: TryOnWearControlSelectionRequest,
    settings: Annotated[Settings, Depends(_settings)],
) -> TryOnWearControlSelectionResponse | JSONResponse:
    """Validate and persist user wear-control selections before generation."""
    try:
        service = _service(settings)
        job = await service.get_job(job_id)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
    if job is None:
        return _error_response(404, _job_not_found_error(job_id))
    if job.status != TryOnJobStatus.ANALYSIS_READY:
        return _error_response(
            409,
            TryOnError(
                code=TryOnErrorCode.RESULT_NOT_READY,
                message="Try-On wear controls can be saved only after pre-generation analysis is ready.",
                details={"job_id": job_id, "status": job.status.value},
            ),
        )
    taxonomy_service = garment_taxonomy_service(settings)
    if taxonomy_service is None:
        return _error_response(
            503,
            TryOnError(
                code=TryOnErrorCode.STORAGE_UNAVAILABLE,
                message="Garment taxonomy storage is not configured.",
                details={"job_id": job_id},
            ),
        )
    slot_by_role = {slot.slot_role: slot.analysis for slot in job.garment_slot_analyses}
    selections: list[TryOnWearControlSelection] = []
    for item in payload.selections:
        analysis = slot_by_role.get(item.slot_role)
        if analysis is None:
            return _error_response(
                422,
                TryOnError(
                    code=TryOnErrorCode.INVALID_GARMENT_COMBINATION,
                    message="Wear-control selection references an unknown garment slot.",
                    details={"job_id": job_id, "slot_role": item.slot_role},
                ),
            )
        try:
            resolved = await taxonomy_service.resolve_selected_control(
                garment_type=analysis.garment_type,
                selected_control_code=item.selected_control_code,
            )
        except ValueError as exc:
            return _error_response(
                422,
                TryOnError(
                    code=TryOnErrorCode.INVALID_GARMENT_COMBINATION,
                    message="Wear-control selection is not allowed for this garment slot.",
                    details={"job_id": job_id, "slot_role": item.slot_role, "reason": str(exc)},
                ),
            )
        selections.append(
            TryOnWearControlSelection(
                slot_role=item.slot_role,
                garment_type=analysis.garment_type,
                requested_control_code=resolved.requested_control_code,
                resolved_control_code=resolved.selected_control.control_code,
                display_name=resolved.selected_control.display_name,
                instruction_template=resolved.selected_control.instruction_template,
                risk_level=resolved.selected_control.risk_level.value,
                resolved_by=resolved.resolved_by,
            )
        )
    updated = job.model_copy(update={"wear_control_selections": selections})
    await service.save_job(updated)
    return TryOnWearControlSelectionResponse(job_id=updated.job_id, status=updated.status, selections=selections)


@router.get("/api/jobs/{job_id}/pre-generation-analysis", response_model=None)
async def get_try_on_pre_generation_analysis(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
) -> TryOnPreGenerationAnalysisResponse | JSONResponse:
    """Return analyzed garment slots and backend-approved wear controls before generation."""
    try:
        job = await _service(settings).get_job(job_id)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
    if job is None:
        return _error_response(404, _job_not_found_error(job_id))
    if job.status != TryOnJobStatus.ANALYSIS_READY:
        return _error_response(
            409,
            TryOnError(
                code=TryOnErrorCode.RESULT_NOT_READY,
                message="Try-On pre-generation analysis is not ready.",
                details={"job_id": job_id, "status": job.status.value},
            ),
        )
    taxonomy_service = garment_taxonomy_service(settings)
    if taxonomy_service is None:
        return _error_response(
            503,
            TryOnError(
                code=TryOnErrorCode.STORAGE_UNAVAILABLE,
                message="Garment taxonomy storage is not configured.",
                details={"job_id": job_id},
            ),
        )

    slots: list[TryOnGarmentSlotWearControlOptions] = []
    for slot_analysis in job.garment_slot_analyses:
        available = await taxonomy_service.resolve_available_controls(
            garment_type=slot_analysis.analysis.garment_type,
        )
        slots.append(
            TryOnGarmentSlotWearControlOptions(
                slot_role=slot_analysis.slot_role,
                garment_type=slot_analysis.analysis.garment_type,
                taxonomy_item_code=available.taxonomy_item.code if available.taxonomy_item else None,
                controls=[_wear_control_response(control) for control in available.available_controls],
            )
        )
    return TryOnPreGenerationAnalysisResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type.value,
        status=job.status,
        slots=slots,
        generate_url=f"/api/jobs/{job.job_id}/generate",
    )


@router.get("/api/jobs/{job_id}/artifacts/result-image", response_model=None)
async def get_try_on_result_image_artifact(
    job_id: str,
    settings: Annotated[Settings, Depends(_settings)],
) -> Response | JSONResponse:
    """Return a browser-safe generated Try-On result image through the backend."""
    try:
        runtime = _runtime(settings)
        job = await runtime.workflow_service.get_job(job_id)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
    if job is None:
        return _error_response(404, _job_not_found_error(job_id))
    if job.status != TryOnJobStatus.COMPLETED or job.result is None:
        body = TryOnNotReadyResponse(
            status="not_ready",
            job_id=job.job_id,
            workflow_type=job.workflow_type,
            current_status=job.status,
            status_url=f"/api/jobs/{job.job_id}/status",
        )
        return JSONResponse(status_code=202, content=body.model_dump(mode="json"))
    if job.result.result_image.kind != "generated_artifact":
        return _error_response(
            404,
            TryOnError(
                code=TryOnErrorCode.JOB_NOT_FOUND,
                message="Try-On generated artifact was not found.",
                details={"job_id": job.job_id, "artifact": "result_image"},
            ),
        )

    object_key = _result_artifact_object_key(
        job_id=job.job_id,
        result_image=job.result.result_image,
        root_prefix=getattr(runtime, "object_storage_root_prefix", getattr(settings, "object_storage_prefix", "fitfabrica")),
    )
    try:
        payload = runtime.object_storage.get_bytes(object_key)
    except Exception:  # noqa: BLE001
        return _error_response(
            404,
            TryOnError(
                code=TryOnErrorCode.JOB_NOT_FOUND,
                message="Try-On generated artifact was not found.",
                details={"job_id": job.job_id, "artifact": "result_image"},
            ),
        )
    return Response(content=payload, media_type=_artifact_media_type(object_key))


def _public_result(*, job_id: str, result: TryOnResult, public_base_url: str) -> TryOnResult:
    """Return a public-safe result payload without internal object-storage URLs."""
    if result.result_image.kind != "generated_artifact":
        return result
    public_image = TryOnResultImage(
        kind=result.result_image.kind,
        url=f"{public_base_url}/api/jobs/{job_id}/artifacts/result-image",
        alt=result.result_image.alt,
    )
    public_image._artifact_object_key = result.result_image._artifact_object_key
    return result.model_copy(update={"result_image": public_image})


def _wear_control_response(control: GarmentWearControl) -> GarmentWearControlResponse:
    """Return one approved wear-control in the public frontend contract."""
    return GarmentWearControlResponse(
        control_code=control.control_code,
        display_name=control.display_name,
        description=control.description,
        instruction_template=control.instruction_template,
        risk_level=control.risk_level,
        default_for_auto=control.default_for_auto,
    )


def _public_base_url(request: Request) -> str:
    """Resolve the browser-visible API origin behind a reverse proxy."""
    forwarded_host = request.headers.get("x-forwarded-host")
    host = (forwarded_host or request.headers.get("host") or request.url.netloc).split(",", 1)[0].strip()
    forwarded_proto = request.headers.get("x-forwarded-proto")
    scheme = (forwarded_proto or request.url.scheme).split(",", 1)[0].strip()
    if not host:
        return str(request.base_url).rstrip("/")
    return f"{scheme}://{host}".rstrip("/")


def _result_artifact_object_key(*, job_id: str, result_image: TryOnResultImage, root_prefix: str) -> str:
    """Resolve the backend-owned result artifact key for generated image delivery."""
    if result_image._artifact_object_key:
        return result_image._artifact_object_key
    parsed_path = urlparse(result_image.url).path
    marker = f"{root_prefix.strip('/')}/tenants/"
    if marker in parsed_path:
        return parsed_path[parsed_path.index(marker) :].lstrip("/")
    filename = "result.png"
    suffix = parsed_path.rsplit("/", 1)[-1]
    if suffix.startswith("result.") and "." in suffix:
        filename = suffix
    return build_media_object_key(
        tenant_id="public",
        workflow="try-on",
        job_id=job_id,
        role="result_image",
        filename=filename,
        root_prefix=root_prefix,
    )


def _artifact_media_type(object_key: str) -> str:
    """Infer the response media type from the stored artifact name."""
    suffix = object_key.rsplit(".", 1)[-1].lower() if "." in object_key else "png"
    if suffix in {"jpg", "jpeg"}:
        return "image/jpeg"
    if suffix == "webp":
        return "image/webp"
    return "image/png"
