"""Mapping helpers between Try-On domain aggregates and SQL rows."""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.try_on import (
    TryOnCostEvent,
    TryOnError,
    TryOnInputMetadata,
    TryOnJob,
    TryOnResult,
    TryOnResultImage,
    TryOnStatusEvent,
    TryOnStoredInput,
)

from .try_on_models import (
    TryOnCostEventRow,
    TryOnErrorRow,
    TryOnJobRow,
    TryOnResultRow,
    TryOnStatusEventRow,
    TryOnStoredInputRow,
)


@dataclass(frozen=True)
class SerializedTryOnJob:
    """Flat SQL row groups derived from one domain aggregate."""

    job_row: TryOnJobRow
    stored_input_rows: list[TryOnStoredInputRow]
    status_event_rows: list[TryOnStatusEventRow]
    cost_event_rows: list[TryOnCostEventRow]
    result_row: TryOnResultRow | None
    error_row: TryOnErrorRow | None


def job_to_models(job: TryOnJob) -> SerializedTryOnJob:
    """Serialize a domain aggregate into focused SQL row groups."""
    return SerializedTryOnJob(
        job_row=TryOnJobRow(
            job_id=job.job_id,
            workflow_type=job.workflow_type.value,
            generation_mode=job.generation_mode.value,
            status=job.status.value,
            input_metadata_json=[item.model_dump(mode="json") for item in job.input_metadata],
            created_at=job.created_at,
            updated_at=job.updated_at,
        ),
        stored_input_rows=[
            TryOnStoredInputRow(
                job_id=job.job_id,
                position=index,
                role=stored_input.role.value,
                storage_backend=stored_input.storage_backend,
                uri=stored_input.uri,
                bucket_name=stored_input.bucket_name,
                object_key=stored_input.object_key,
                object_name=stored_input.object_name,
                content_type=stored_input.content_type,
                size_bytes=stored_input.size_bytes,
                sha256=stored_input.sha256,
                created_at=stored_input.created_at,
            )
            for index, stored_input in enumerate(job.stored_inputs)
        ],
        status_event_rows=[
            TryOnStatusEventRow(
                job_id=job.job_id,
                position=index,
                status=event.status.value,
                stage=event.stage,
                message=event.message,
                occurred_at=event.occurred_at,
            )
            for index, event in enumerate(job.status_history)
        ],
        cost_event_rows=[
            TryOnCostEventRow(
                job_id=job.job_id,
                position=index,
                event_type=event.event_type,
                estimated_units=event.estimated_units,
                charge_status=event.charge_status.value,
                charged_credits=event.charged_credits,
                occurred_at=event.occurred_at,
            )
            for index, event in enumerate(job.cost_events)
        ],
        result_row=(
            TryOnResultRow(
                job_id=job.job_id,
                result_image_json=job.result.result_image.model_dump(mode="json"),
                quality_report_json=job.result.quality_report.model_dump(mode="json"),
                stylist_note=job.result.stylist_note,
                input_metadata_json=[item.model_dump(mode="json") for item in job.result.input_metadata],
                completed_at=job.result.completed_at,
            )
            if job.result is not None
            else None
        ),
        error_row=(
            TryOnErrorRow(
                job_id=job.job_id,
                code=job.error.code.value,
                message=job.error.message,
                details_json=dict(job.error.details),
            )
            if job.error is not None
            else None
        ),
    )


def job_from_models(
    *,
    job_row: TryOnJobRow,
    stored_input_rows: list[TryOnStoredInputRow],
    status_event_rows: list[TryOnStatusEventRow],
    cost_event_rows: list[TryOnCostEventRow],
    result_row: TryOnResultRow | None,
    error_row: TryOnErrorRow | None,
) -> TryOnJob:
    """Reconstruct a Try-On domain aggregate from SQL rows."""
    result = None
    if result_row is not None:
        result = TryOnResult(
            job_id=job_row.job_id,
            workflow_type=job_row.workflow_type,
            result_image=TryOnResultImage.model_validate(result_row.result_image_json),
            quality_report=result_row.quality_report_json,
            stylist_note=result_row.stylist_note,
            input_metadata=[TryOnInputMetadata.model_validate(item) for item in result_row.input_metadata_json],
            completed_at=result_row.completed_at,
        )

    error = None
    if error_row is not None:
        error = TryOnError(
            code=error_row.code,
            message=error_row.message,
            details=dict(error_row.details_json or {}),
        )

    return TryOnJob(
        job_id=job_row.job_id,
        workflow_type=job_row.workflow_type,
        generation_mode=job_row.generation_mode,
        status=job_row.status,
        created_at=job_row.created_at,
        updated_at=job_row.updated_at,
        input_metadata=[TryOnInputMetadata.model_validate(item) for item in job_row.input_metadata_json],
        stored_inputs=[
            TryOnStoredInput(
                role=row.role,
                storage_backend=row.storage_backend,
                uri=row.uri,
                bucket_name=row.bucket_name,
                object_key=row.object_key,
                object_name=row.object_name,
                content_type=row.content_type,
                size_bytes=row.size_bytes,
                sha256=row.sha256,
                created_at=row.created_at,
            )
            for row in sorted(stored_input_rows, key=lambda item: item.position)
        ],
        status_history=[
            TryOnStatusEvent(
                status=row.status,
                stage=row.stage,
                message=row.message,
                occurred_at=row.occurred_at,
            )
            for row in sorted(status_event_rows, key=lambda item: item.position)
        ],
        cost_events=[
            TryOnCostEvent(
                event_type=row.event_type,
                estimated_units=row.estimated_units,
                charge_status=row.charge_status,
                charged_credits=row.charged_credits,
                occurred_at=row.occurred_at,
            )
            for row in sorted(cost_event_rows, key=lambda item: item.position)
        ],
        result=result,
        error=error,
    )
