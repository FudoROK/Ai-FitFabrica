from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.adapters.database.sql.base import SqlBase
from src.adapters.database.sql.try_on_repositories import SqlTryOnJobRepository
from src.domain.try_on import (
    TryOnChargeStatus,
    TryOnCostEvent,
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnJob,
    TryOnJobStatus,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStatusEvent,
    TryOnStoredInput,
    TryOnUploadRole,
    TryOnWorkflowType,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _job() -> TryOnJob:
    metadata = [
        TryOnInputMetadata(
            role=TryOnUploadRole.HUMAN_PHOTO,
            filename="human.png",
            content_type="image/png",
            size_bytes=32,
            sha256="a" * 64,
        ),
        TryOnInputMetadata(
            role=TryOnUploadRole.GARMENT_PHOTO,
            filename="garment.png",
            content_type="image/png",
            size_bytes=48,
            sha256="b" * 64,
        ),
    ]
    return TryOnJob(
        job_id="try_on_123",
        workflow_type=TryOnWorkflowType.TRY_ON,
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        status=TryOnJobStatus.COMPLETED,
        created_at=_utc_now(),
        updated_at=_utc_now(),
        input_metadata=metadata,
        stored_inputs=[
            TryOnStoredInput(
                role=TryOnUploadRole.HUMAN_PHOTO,
                storage_backend="s3",
                uri="s3://bucket/tenant/job/human.png",
                bucket_name="bucket",
                object_key="tenant/job/human.png",
                object_name="tenant/job/human.png",
                content_type="image/png",
                size_bytes=32,
                sha256="a" * 64,
            )
        ],
        status_history=[
            TryOnStatusEvent(status=TryOnJobStatus.ACCEPTED, stage="accepted", message="Accepted."),
            TryOnStatusEvent(status=TryOnJobStatus.COMPLETED, stage="completed", message="Completed."),
        ],
        cost_events=[
            TryOnCostEvent(
                event_type="try_on_sandbox_generation",
                estimated_units=1,
                charge_status=TryOnChargeStatus.NOT_CHARGED,
                charged_credits=0,
            )
        ],
        result=TryOnResult(
            job_id="try_on_123",
            workflow_type=TryOnWorkflowType.TRY_ON,
            result_image=TryOnResultImage(
                kind="sandbox_placeholder",
                url="/images/shared/try-on-sandbox-result.webp",
                alt="Sandbox Try-On result preview",
            ),
            quality_report=TryOnQualityReport(
                verdict="pass",
                confidence=0.9,
                checks=[
                    TryOnQualityCheck(
                        name="face_preservation",
                        status="passed",
                        confidence=0.9,
                        message="OK",
                    )
                ],
                limitations=[],
            ),
            stylist_note="Sandbox complete.",
            input_metadata=metadata,
            completed_at=_utc_now(),
        ),
        error=None,
    )


@pytest.mark.asyncio
async def test_sql_try_on_repository_round_trips_job_aggregate() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(SqlBase.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    repository = SqlTryOnJobRepository(session_factory=session_factory)
    job = _job()

    await repository.save(job)
    saved = await repository.get(job.job_id)

    assert saved is not None
    assert saved.job_id == job.job_id
    assert saved.generation_mode == TryOnGenerationMode.SANDBOX_FAKE
    assert saved.stored_inputs[0].object_key == "tenant/job/human.png"
    assert saved.result is not None
    assert saved.result.result_image.url == "/images/shared/try-on-sandbox-result.webp"

    await engine.dispose()
