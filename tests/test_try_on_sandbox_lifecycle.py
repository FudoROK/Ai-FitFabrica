from fastapi.testclient import TestClient

from src.domain.try_on import (
    TryOnChargeStatus,
    TryOnCostEvent,
    TryOnInputMetadata,
    TryOnJob,
    TryOnJobCreatedResponse,
    TryOnJobStatus,
    TryOnJobStatusResponse,
    TryOnNotReadyResponse,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnResultResponse,
    TryOnStatusEvent,
    TryOnUploadRole,
    TryOnWorkflowType,
    utc_now,
)
from src.main import app


client = TestClient(app)


def test_try_on_missing_files_returns_typed_error():
    response = client.post("/api/try-on/jobs", files={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "missing_required_file"
    assert body["error"]["details"]["fields"] == ["human_photo", "garment_photo"]


def test_try_on_rejects_unsupported_content_type():
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.txt", b"hello", "text/plain"),
            "garment_photo": ("garment.png", b"fake-image", "image/png"),
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "unsupported_content_type"
    assert body["error"]["details"]["field"] == "human_photo"


def test_try_on_domain_contracts_match_planned_shapes():
    human_metadata = TryOnInputMetadata(
        role=TryOnUploadRole.HUMAN_PHOTO,
        filename="human.png",
        content_type="image/png",
        size_bytes=128,
        sha256="a" * 64,
    )
    garment_metadata = TryOnInputMetadata(
        role=TryOnUploadRole.GARMENT_PHOTO,
        filename="garment.webp",
        content_type="image/webp",
        size_bytes=256,
        sha256="b" * 64,
    )
    status_event = TryOnStatusEvent(
        status=TryOnJobStatus.ACCEPTED,
        stage="accepted",
        message="Job accepted.",
    )
    cost_event = TryOnCostEvent(
        event_type="sandbox_job_created",
        estimated_units=0,
        charge_status=TryOnChargeStatus.NOT_CHARGED,
        charged_credits=0,
    )
    quality_report = TryOnQualityReport(
        verdict="pass",
        confidence=1.0,
        checks=[
            TryOnQualityCheck(
                name="sandbox_placeholder",
                status="passed",
                confidence=1.0,
                message="Deterministic placeholder accepted.",
            )
        ],
        limitations=["No real generation was performed."],
    )
    result = TryOnResult(
        job_id="job_123",
        workflow_type=TryOnWorkflowType.TRY_ON,
        result_image=TryOnResultImage(
            kind="sandbox_placeholder",
            url="/api/try-on/jobs/job_123/result/image",
            alt="Sandbox try-on placeholder",
        ),
        quality_report=quality_report,
        stylist_note="Sandbox result.",
        input_metadata=[human_metadata, garment_metadata],
        completed_at=utc_now(),
    )
    job = TryOnJob(
        job_id="job_123",
        workflow_type=TryOnWorkflowType.TRY_ON,
        status=TryOnJobStatus.COMPLETED,
        created_at=utc_now(),
        updated_at=utc_now(),
        input_metadata=[human_metadata, garment_metadata],
        status_history=[status_event],
        cost_events=[cost_event],
        result=result,
        error=None,
    )

    created_response = TryOnJobCreatedResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        status=job.status,
        input_metadata=job.input_metadata,
        status_url=f"/api/try-on/jobs/{job.job_id}",
        result_url=f"/api/try-on/jobs/{job.job_id}/result",
    )
    status_response = TryOnJobStatusResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        status=job.status,
        status_history=job.status_history,
        cost_events=job.cost_events,
    )
    result_response = TryOnResultResponse(
        status="completed",
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        result=result,
    )
    not_ready_response = TryOnNotReadyResponse(
        status="not_ready",
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        current_status=TryOnJobStatus.GENERATING,
        status_url=f"/api/try-on/jobs/{job.job_id}",
    )

    assert created_response.input_metadata[0].sha256 == "a" * 64
    assert status_response.status_history[0].stage == "accepted"
    assert result_response.result.result_image.kind == "sandbox_placeholder"
    assert not_ready_response.current_status == TryOnJobStatus.GENERATING
