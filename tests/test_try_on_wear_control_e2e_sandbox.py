from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO

import pytest
from starlette.datastructures import UploadFile

from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.garment_taxonomy import GarmentTaxonomyItem, GarmentWearControl
from src.domain.try_on import TryOnJobStatus, TryOnSandboxLifecycleMode, TryOnWearControlSelection
from src.use_cases.garment_taxonomy.service import GarmentTaxonomyService
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from tests.try_on_analysis_bundle_stub import required_analysis_bundle
from tests.try_on_human_identity_stub import AllowingHumanIdentityAnalysisStub


@pytest.mark.anyio
async def test_try_on_wear_control_sandbox_acceptance_analysis_selection_generation_result() -> None:
    repository = InMemoryTryOnJobRepository()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        analysis_bundle_service=required_analysis_bundle(AllowingHumanIdentityAnalysisStub()),
        instruction_creator=DeterministicTryOnInstructionAdapter(),
        file_storage=InMemoryTryOnFileStorage(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg", "image/png", "image/webp"},
            max_upload_bytes=1024,
        ),
    )
    taxonomy = GarmentTaxonomyService(repository=_taxonomy_repository())

    created = await service.create_job(
        human_photo=_upload_file("human.png", b"human-image", "image/png"),
        garment_photo=_upload_file("garment.png", b"garment-image", "image/png"),
    )
    analyzed = await service.execute_job(
        job_id=created.job_id,
        lifecycle_mode=TryOnSandboxLifecycleMode.ANALYSIS_ONLY,
    )
    assert analyzed.status == TryOnJobStatus.ANALYSIS_READY
    assert analyzed.garment_slot_analyses[0].analysis.garment_type == "test garment"

    resolved = await taxonomy.resolve_selected_control(
        garment_type=analyzed.garment_slot_analyses[0].analysis.garment_type,
        selected_control_code="relaxed_drape",
    )
    with_selection = analyzed.model_copy(
        update={
            "wear_control_selections": [
                TryOnWearControlSelection(
                    slot_role=analyzed.garment_slot_analyses[0].slot_role,
                    garment_type=analyzed.garment_slot_analyses[0].analysis.garment_type,
                    requested_control_code=resolved.requested_control_code,
                    resolved_control_code=resolved.selected_control.control_code,
                    display_name=resolved.selected_control.display_name,
                    instruction_template=resolved.selected_control.instruction_template,
                    risk_level=resolved.selected_control.risk_level.value,
                    resolved_by=resolved.resolved_by,
                )
            ]
        }
    )
    await service.save_job(with_selection)

    completed = await service.execute_job(job_id=created.job_id)

    assert completed.status == TryOnJobStatus.COMPLETED
    assert completed.result is not None
    assert completed.instruction is not None
    assert completed.instruction.outfit_slot_focus_points[0].focus_points == [
        "Keep the test garment relaxed and untucked over the base outfit."
    ]
    assert completed.result.quality_report.verdict == "pass"
    assert [event.status for event in completed.status_history] == [
        TryOnJobStatus.ACCEPTED,
        TryOnJobStatus.ANALYZING_HUMAN,
        TryOnJobStatus.ANALYSIS_READY,
        TryOnJobStatus.GENERATING,
        TryOnJobStatus.QUALITY_CHECKING,
        TryOnJobStatus.COMPLETED,
    ]


@dataclass
class _TaxonomyRepository:
    items: dict[str, GarmentTaxonomyItem] = field(default_factory=dict)
    controls: list[GarmentWearControl] = field(default_factory=list)

    async def get_item_by_code(self, code: str) -> GarmentTaxonomyItem | None:
        return self.items.get(code)

    async def list_controls_for_item_or_parent(self, code: str) -> list[GarmentWearControl]:
        return [control for control in self.controls if control.taxonomy_item_code == code]


def _taxonomy_repository() -> _TaxonomyRepository:
    return _TaxonomyRepository(
        items={
            "test_garment": GarmentTaxonomyItem(
                code="test_garment",
                category="tops",
                display_name="Test garment",
            )
        },
        controls=[
            GarmentWearControl(
                taxonomy_item_code="test_garment",
                control_code="relaxed_drape",
                display_name="Relaxed drape",
                instruction_template="Keep the test garment relaxed and untucked over the base outfit.",
                default_for_auto=True,
            )
        ],
    )


def _upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(filename=filename, file=BytesIO(content), headers={"content-type": content_type})
