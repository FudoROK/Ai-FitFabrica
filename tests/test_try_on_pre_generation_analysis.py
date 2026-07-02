from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.datastructures import UploadFile

from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.garment_taxonomy import GarmentTaxonomyItem, GarmentWearControl
from src.domain.try_on import TryOnJob, TryOnJobStatus, TryOnSandboxLifecycleMode, TryOnStatusEvent
from src.entrypoints.try_on_routes import router
from src.use_cases.garment_taxonomy.service import AvailableWearControlsResult
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from tests.try_on_analysis_bundle_stub import approved_analysis_bundle, required_analysis_bundle
from tests.try_on_human_identity_stub import AllowingHumanIdentityAnalysisStub


@pytest.mark.anyio
async def test_try_on_analysis_only_stops_before_generation_and_persists_slot_analysis() -> None:
    service = _workflow_service()
    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.png", b"garment-image", "image/png"),
    )

    analyzed = await service.execute_job(
        job_id=job.job_id,
        lifecycle_mode=TryOnSandboxLifecycleMode.ANALYSIS_ONLY,
    )

    assert analyzed.status == TryOnJobStatus.ANALYSIS_READY
    assert analyzed.result is None
    assert analyzed.instruction is None
    assert analyzed.garment_slot_analyses
    assert [event.status for event in analyzed.status_history] == [
        TryOnJobStatus.ACCEPTED,
        TryOnJobStatus.ANALYZING_HUMAN,
        TryOnJobStatus.ANALYSIS_READY,
    ]
    assert analyzed.cost_events[0].charged_credits == 0


@pytest.mark.anyio
async def test_try_on_generation_resumes_from_persisted_analysis_without_rerunning_analysis() -> None:
    repository = InMemoryTryOnJobRepository()
    service = _workflow_service(repository=repository)
    job = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.png", b"garment-image", "image/png"),
    )
    analyzed = await service.execute_job(
        job_id=job.job_id,
        lifecycle_mode=TryOnSandboxLifecycleMode.ANALYSIS_ONLY,
    )

    completed = await service.execute_job(job_id=analyzed.job_id)

    assert completed.status == TryOnJobStatus.COMPLETED
    assert completed.result is not None
    assert [event.status for event in completed.status_history] == [
        TryOnJobStatus.ACCEPTED,
        TryOnJobStatus.ANALYZING_HUMAN,
        TryOnJobStatus.ANALYSIS_READY,
        TryOnJobStatus.GENERATING,
        TryOnJobStatus.QUALITY_CHECKING,
        TryOnJobStatus.COMPLETED,
    ]


def test_pre_generation_analysis_route_returns_slot_controls(monkeypatch) -> None:
    client = _route_client(monkeypatch, _RouteService(_analysis_ready_job()), _TaxonomyService())

    response = client.get("/api/jobs/job-1/pre-generation-analysis")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-1",
        "workflow_type": "try_on",
        "status": "analysis_ready",
        "slots": [
            {
                "slot_role": "garment_photo",
                "garment_type": "coat",
                "taxonomy_item_code": "coat",
                "selected_control_code": "auto",
                "controls": [
                    {
                        "control_code": "open_front",
                        "display_name": "Open front",
                        "description": "Wear the coat open.",
                        "instruction_template": "Keep the coat open without hiding the base outfit.",
                        "risk_level": "low",
                        "default_for_auto": True,
                    }
                ],
            }
        ],
        "generate_url": "/api/jobs/job-1/generate",
    }


def test_pre_generation_analysis_route_blocks_before_analysis_ready(monkeypatch) -> None:
    job = _analysis_ready_job().model_copy(update={"status": TryOnJobStatus.ACCEPTED})
    client = _route_client(monkeypatch, _RouteService(job), _TaxonomyService())

    response = client.get("/api/jobs/job-1/pre-generation-analysis")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "result_not_ready"


def test_wear_control_selection_route_persists_validated_backend_selection(monkeypatch) -> None:
    service = _RouteService(_analysis_ready_job())
    client = _route_client(monkeypatch, service, _TaxonomyService())

    response = client.put(
        "/api/jobs/job-1/wear-controls",
        json={"selections": [{"slot_role": "garment_photo", "selected_control_code": "open_front"}]},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["selections"][0]["slot_role"] == "garment_photo"
    assert payload["selections"][0]["resolved_control_code"] == "open_front"
    assert service.saved_job is not None
    assert service.saved_job.wear_control_selections[0].instruction_template == (
        "Keep the coat open without hiding the base outfit."
    )


def test_wear_control_selection_route_rejects_unknown_slot(monkeypatch) -> None:
    client = _route_client(monkeypatch, _RouteService(_analysis_ready_job()), _TaxonomyService())

    response = client.put(
        "/api/jobs/job-1/wear-controls",
        json={"selections": [{"slot_role": "missing_slot", "selected_control_code": "open_front"}]},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_garment_combination"


class _RouteService:
    def __init__(self, job: TryOnJob) -> None:
        self._job = job
        self.saved_job: TryOnJob | None = None

    async def get_job(self, job_id: str) -> TryOnJob | None:
        return self._job if job_id == self._job.job_id else None

    async def save_job(self, job: TryOnJob) -> None:
        self.saved_job = job
        self._job = job


class _TaxonomyService:
    async def resolve_available_controls(self, *, garment_type: str, unknown_input=None):
        item = GarmentTaxonomyItem(code=garment_type, category="outerwear", display_name="Coat")
        return AvailableWearControlsResult(
            taxonomy_item=item,
            available_controls=[
                GarmentWearControl(
                    control_code="open_front",
                    display_name="Open front",
                    description="Wear the coat open.",
                    instruction_template="Keep the coat open without hiding the base outfit.",
                    taxonomy_item_code=item.code,
                    default_for_auto=True,
                )
            ],
        )

    async def resolve_selected_control(self, *, garment_type: str, selected_control_code: str):
        from src.use_cases.garment_taxonomy.service import SelectedWearControlResult

        available = await self.resolve_available_controls(garment_type=garment_type)
        control = available.available_controls[0]
        if selected_control_code not in {"auto", control.control_code}:
            raise ValueError("control is not allowed")
        return SelectedWearControlResult(
            requested_control_code=selected_control_code,
            selected_control=control,
            resolved_by="backend_auto_default" if selected_control_code == "auto" else "user_selection",
        )


def _route_client(monkeypatch, service: _RouteService, taxonomy_service: _TaxonomyService) -> TestClient:
    app = FastAPI()
    app.state.settings = SimpleNamespace()
    app.include_router(router)
    monkeypatch.setattr("src.entrypoints.try_on_routes._service", lambda settings: service)
    monkeypatch.setattr("src.entrypoints.try_on_routes.garment_taxonomy_service", lambda settings: taxonomy_service)
    return TestClient(app)


def _workflow_service(repository: InMemoryTryOnJobRepository | None = None) -> TryOnWorkflowService:
    return TryOnWorkflowService(
        repository=repository or InMemoryTryOnJobRepository(),
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )


def _analysis_ready_job() -> TryOnJob:
    bundle = approved_analysis_bundle()
    return TryOnJob(
        job_id="job-1",
        status=TryOnJobStatus.ANALYSIS_READY,
        status_history=[
            TryOnStatusEvent(
                status=TryOnJobStatus.ANALYSIS_READY,
                stage="analysis_ready",
                message="Input analysis is ready.",
            )
        ],
        human_identity_analysis=bundle.human_identity,
        garment_identity_analysis=bundle.garment_identity,
        garment_slot_analyses=bundle.garment_slot_analyses,
        material_texture_analysis=bundle.material_texture,
    )


def _upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), headers={"content-type": content_type})
