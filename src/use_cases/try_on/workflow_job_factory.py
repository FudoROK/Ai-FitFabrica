"""Job/event construction helpers for the Try-On workflow service."""
from __future__ import annotations

from src.domain.try_on import (
    TryOnChargeStatus,
    TryOnCostEvent,
    TryOnError,
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnJob,
    TryOnJobStatus,
    TryOnResult,
    TryOnStatusEvent,
    TryOnStoredInput,
    TryOnWorkflowType,
    utc_now,
)


def build_job(
    *,
    job_id: str,
    status: TryOnJobStatus,
    input_metadata: list[TryOnInputMetadata],
    stored_inputs: list[TryOnStoredInput],
    status_history: list[TryOnStatusEvent],
    result: TryOnResult | None,
    error: TryOnError | None,
    generation_mode: TryOnGenerationMode,
    charged_credits: int = 0,
) -> TryOnJob:
    """Build a Try-On job with common cost bookkeeping."""
    now = utc_now()
    return TryOnJob(
        job_id=job_id,
        workflow_type=TryOnWorkflowType.TRY_ON,
        generation_mode=generation_mode,
        status=status,
        created_at=now,
        updated_at=now,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        status_history=status_history,
        cost_events=[
            cost_event(
                estimated_units=1 if status == TryOnJobStatus.COMPLETED else 0,
                charged_credits=charged_credits,
            )
        ],
        result=result,
        error=error,
    )


def status_event(
    status: TryOnJobStatus,
    message: str,
    *,
    generation_mode: TryOnGenerationMode = TryOnGenerationMode.SANDBOX_FAKE,
) -> TryOnStatusEvent:
    """Build a status event with the canonical stage value."""
    stages = {
        TryOnJobStatus.ACCEPTED: "accepted",
        TryOnJobStatus.ANALYZING_HUMAN: "human_identity_analysis",
        TryOnJobStatus.ANALYSIS_READY: "analysis_ready",
        TryOnJobStatus.GENERATING: _generation_stage(generation_mode),
        TryOnJobStatus.QUALITY_CHECKING: "quality_check",
        TryOnJobStatus.REPAIRING: "repair",
        TryOnJobStatus.COMPLETED: "completed",
        TryOnJobStatus.FAILED: "failed",
    }
    return TryOnStatusEvent(status=status, stage=stages[status], message=message)


def cost_event(
    *,
    estimated_units: int = 0,
    charged_credits: int = 0,
    generation_mode: TryOnGenerationMode = TryOnGenerationMode.SANDBOX_FAKE,
) -> TryOnCostEvent:
    """Build the canonical cost event for one Try-On generation attempt."""
    return TryOnCostEvent(
        event_type=_generation_cost_event_type(generation_mode),
        estimated_units=estimated_units,
        charge_status=TryOnChargeStatus.CHARGED if charged_credits > 0 else TryOnChargeStatus.NOT_CHARGED,
        charged_credits=charged_credits,
    )


def repair_cost_event(*, estimated_units: int = 1, charged_credits: int = 0) -> TryOnCostEvent:
    """Build the canonical cost event for provider-runtime image-editing repair."""
    return TryOnCostEvent(
        event_type="try_on_provider_runtime_image_editing_repair",
        estimated_units=estimated_units,
        charge_status=TryOnChargeStatus.CHARGED if charged_credits > 0 else TryOnChargeStatus.NOT_CHARGED,
        charged_credits=charged_credits,
    )


def _generation_stage(generation_mode: TryOnGenerationMode) -> str:
    """Return the status-history stage for the configured generation backend."""
    if generation_mode == TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON:
        return "vertex_virtual_try_on_generation"
    if generation_mode == TryOnGenerationMode.PROVIDER_RUNTIME:
        return "provider_runtime_generation"
    return "sandbox_generation"


def _generation_cost_event_type(generation_mode: TryOnGenerationMode) -> str:
    """Return the cost event type while preserving the original sandbox contract."""
    if generation_mode == TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON:
        return "try_on_vertex_virtual_try_on_generation"
    if generation_mode == TryOnGenerationMode.PROVIDER_RUNTIME:
        return "try_on_provider_runtime_generation"
    return "try_on_sandbox_generation"
