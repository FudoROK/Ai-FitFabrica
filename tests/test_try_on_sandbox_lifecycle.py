from io import BytesIO

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest
from starlette.datastructures import UploadFile

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
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
from src.settings import Settings
from src.use_cases.try_on.workflow_service import (
    TryOnUploadValidationConfig,
    TryOnValidationError,
    TryOnWorkflowService,
)


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


def test_try_on_rejects_empty_file():
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.png", b"", "image/png"),
            "garment_photo": ("garment.png", b"fake-image", "image/png"),
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "empty_file"
    assert body["error"]["details"]["field"] == "human_photo"


def test_try_on_unknown_status_job_returns_typed_error():
    response = client.get("/api/jobs/missing/status")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "job_not_found"
    assert body["error"]["details"]["job_id"] == "missing"


def test_try_on_unknown_result_job_returns_typed_error():
    response = client.get("/api/jobs/missing/result")

    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "job_not_found"
    assert body["error"]["details"]["job_id"] == "missing"


def test_try_on_job_creation_records_status_history_and_cost_events():
    """Route lifecycle should expose completed status history and cost events."""
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.png", b"human-image", "image/png"),
            "garment_photo": ("garment.webp", b"garment-image", "image/webp"),
        },
    )

    assert response.status_code == 202
    created = response.json()
    assert created["status"] == "accepted"
    status_response = client.get(created["status_url"])

    assert status_response.status_code == 200
    body = status_response.json()
    assert body["status"] == "completed"
    assert [event["status"] for event in body["status_history"]] == [
        "accepted",
        "generating",
        "quality_checking",
        "completed",
    ]
    assert body["cost_events"] == [
        {
            "event_type": "try_on_sandbox_generation",
            "estimated_units": 1,
            "charge_status": "not_charged",
            "charged_credits": 0,
            "occurred_at": body["cost_events"][0]["occurred_at"],
        }
    ]


def test_try_on_result_contract_is_structurally_realistic():
    """Route result should expose a realistic completed sandbox result contract."""
    create_response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.jpg", b"human-image", "image/jpeg"),
            "garment_photo": ("garment.png", b"garment-image", "image/png"),
        },
    )

    assert create_response.status_code == 202
    result_response = client.get(create_response.json()["result_url"])

    assert result_response.status_code == 200
    body = result_response.json()
    result = body["result"]
    assert body["status"] == "completed"
    assert result["result_image"] == {
        "kind": "sandbox_placeholder",
        "url": "/images/shared/try-on-sandbox-result.webp",
        "alt": "Sandbox Try-On result preview",
    }
    assert result["quality_report"]["verdict"] == "pass"
    assert result["quality_report"]["checks"][0]["name"] == "face_preservation"
    assert result["stylist_note"]
    assert [item["role"] for item in result["input_metadata"]] == ["human_photo", "garment_photo"]


def test_try_on_public_responses_do_not_expose_storage_references():
    """Storage object references must stay internal to the backend job aggregate."""
    create_response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.jpg", b"human-image", "image/jpeg"),
            "garment_photo": ("garment.png", b"garment-image", "image/png"),
        },
    )

    assert create_response.status_code == 202
    created = create_response.json()
    status_response = client.get(created["status_url"])
    result_response = client.get(created["result_url"])

    assert status_response.status_code == 200
    assert result_response.status_code == 200
    public_bodies = [created, status_response.json(), result_response.json()]
    serialized = " ".join(str(body) for body in public_bodies)

    assert "stored_inputs" not in serialized
    assert "memory://try-on/" not in serialized
    assert "bucket_name" not in serialized
    assert "object_key" not in serialized
    assert "object_name" not in serialized


def test_try_on_pending_sandbox_job_returns_not_ready_result():
    """Sandbox should expose a non-completed job path for async frontend polling."""
    create_response = client.post(
        "/api/try-on/jobs",
        data={"sandbox_lifecycle_mode": "pending"},
        files={
            "human_photo": ("human.jpg", b"human-image", "image/jpeg"),
            "garment_photo": ("garment.png", b"garment-image", "image/png"),
        },
    )

    assert create_response.status_code == 202
    created = create_response.json()
    assert created["status"] == "accepted"

    result_response = client.get(created["result_url"])

    assert result_response.status_code == 202
    body = result_response.json()
    assert body == {
        "status": "not_ready",
        "job_id": created["job_id"],
        "workflow_type": "try_on",
        "current_status": "accepted",
        "status_url": created["status_url"],
    }

    status_response = client.get(created["status_url"])
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["status"] == "accepted"
    assert [event["status"] for event in status_body["status_history"]] == [
        "accepted",
    ]
    assert status_body["cost_events"][0]["charge_status"] == "not_charged"


def test_try_on_failed_sandbox_job_returns_typed_result_error():
    """Sandbox should expose a failed job path for frontend error handling."""
    create_response = client.post(
        "/api/try-on/jobs",
        data={"sandbox_lifecycle_mode": "failed"},
        files={
            "human_photo": ("human.jpg", b"human-image", "image/jpeg"),
            "garment_photo": ("garment.png", b"garment-image", "image/png"),
        },
    )

    assert create_response.status_code == 202
    created = create_response.json()
    assert created["status"] == "accepted"

    result_response = client.get(created["result_url"])

    assert result_response.status_code == 409
    body = result_response.json()
    assert body["error"]["code"] == "job_failed"
    assert body["error"]["details"]["job_id"] == created["job_id"]

    status_response = client.get(created["status_url"])
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["status"] == "failed"
    assert status_body["status_history"][-1]["status"] == "failed"


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


def test_try_on_settings_content_types_fallback_and_positive_upload_limit():
    settings = Settings(
        _env_file=None,
        GCP_PROJECT_ID="project",
        PUBSUB_TOPIC_NAME="topic",
        TRY_ON_ALLOWED_CONTENT_TYPES=",",
    )

    assert settings.try_on_allowed_content_types == ["image/jpeg", "image/png", "image/webp"]

    try:
        Settings(
            _env_file=None,
            GCP_PROJECT_ID="project",
            PUBSUB_TOPIC_NAME="topic",
            TRY_ON_MAX_UPLOAD_BYTES=0,
        )
    except ValidationError as exc:
        error = exc.errors()[0]
        assert error["loc"] == ("TRY_ON_MAX_UPLOAD_BYTES",)
        assert error["type"] == "greater_than"
    else:
        raise AssertionError("TRY_ON_MAX_UPLOAD_BYTES=0 must be rejected")


def test_try_on_input_metadata_rejects_non_hex_sha256():
    try:
        TryOnInputMetadata(
            role=TryOnUploadRole.HUMAN_PHOTO,
            filename="human.png",
            content_type="image/png",
            size_bytes=128,
            sha256="z" * 64,
        )
    except ValidationError as exc:
        assert "sha256" in str(exc)
    else:
        raise AssertionError("sha256 must reject non-hex values")


def _upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    """Build an in-memory UploadFile for direct workflow service tests."""
    return UploadFile(filename=filename, file=BytesIO(content), headers={"content-type": content_type})


def _service() -> tuple[TryOnWorkflowService, InMemoryTryOnJobRepository]:
    """Build the Try-On workflow service with in-memory sandbox adapters."""
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )
    return service, repository


@pytest.mark.anyio
async def test_try_on_workflow_service_creates_completed_job_and_persists_it():
    """Service should validate two uploads, complete the workflow, and persist the job."""
    service, repository = _service()

    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.webp", b"garment-image", "image/webp"),
    )
    completed = await service.execute_job(job_id=job.job_id)

    assert job.status == TryOnJobStatus.ACCEPTED
    assert [event.status for event in completed.status_history] == [
        TryOnJobStatus.ACCEPTED,
        TryOnJobStatus.GENERATING,
        TryOnJobStatus.QUALITY_CHECKING,
        TryOnJobStatus.COMPLETED,
    ]
    assert [event.stage for event in completed.status_history] == [
        "accepted",
        "sandbox_generation",
        "quality_check",
        "completed",
    ]
    assert completed.cost_events[0].event_type == "try_on_sandbox_generation"
    assert completed.cost_events[0].charge_status == TryOnChargeStatus.NOT_CHARGED
    assert completed.cost_events[0].charged_credits == 0
    assert completed.result is not None
    assert completed.result.quality_report.verdict == "pass"
    assert completed.result.quality_report.checks[0] == TryOnQualityCheck(
        name="face_preservation",
        status="passed",
        confidence=0.92,
        message="Sandbox verifier confirms the face-preservation check shape.",
    )
    assert completed.result.quality_report.checks[1] == TryOnQualityCheck(
        name="garment_similarity",
        status="passed",
        confidence=0.9,
        message="Sandbox verifier confirms garment-similarity reporting shape.",
    )
    assert completed.result.quality_report.checks[2] == TryOnQualityCheck(
        name="artifact_scan",
        status="warning",
        confidence=0.74,
        message="Sandbox output is deterministic and not a real image generation.",
    )
    assert completed.result.quality_report.limitations == ["Sandbox fake generation does not evaluate the uploaded pixels."]
    assert (
        completed.result.stylist_note
        == "Sandbox Try-On completed. Real stylist advice will be generated after the production generation adapter is connected."
    )
    assert await repository.get(job.job_id) == completed


@pytest.mark.anyio
async def test_try_on_workflow_service_rejects_unsupported_content_type():
    """Service should reject unsupported upload content types with a typed error."""
    service, _repository = _service()

    with pytest.raises(TryOnValidationError) as exc_info:
        await service.create_job(
            human_photo=_upload_file("human.txt", b"human-image", "text/plain"),
            garment_photo=_upload_file("garment.webp", b"garment-image", "image/webp"),
        )

    assert exc_info.value.error.code == "unsupported_content_type"


@pytest.mark.anyio
async def test_try_on_workflow_service_get_job_returns_none_for_missing_job():
    """Service should leave missing-job response mapping to the route layer."""
    service, _repository = _service()

    assert await service.get_job("missing") is None
