"""Guardrails for backend-driven Try-On wear-control UI."""

from pathlib import Path

from tests.frontend_api_sources import api_client_source


def test_try_on_workspace_uses_backend_driven_wear_control_picker() -> None:
    workflow_source = Path("apps/web/src/features/workspace/try-on-workflow.tsx").read_text(encoding="utf-8")
    picker_source = Path("apps/web/src/features/workspace/garment-wear-control-picker.tsx").read_text(encoding="utf-8")
    client_source = api_client_source()
    contracts_source = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")

    assert "GarmentWearControlPicker" in workflow_source
    assert "wear-control-pending-analysis" in picker_source
    assert "getGarmentWearControls" in client_source
    assert "saveTryOnWearControls" in client_source
    assert "continueTryOnGeneration" in client_source
    assert "/api/garment-taxonomy/wear-controls" in client_source
    assert "/api/jobs/${encodeURIComponent(jobId)}/wear-controls" in client_source
    assert "GarmentWearControlListResponse" in contracts_source
    assert "TryOnWearControlSelectionRequest" in contracts_source

    for slot_role in (
        "garment_photo",
        "upper_garment_photo",
        "lower_garment_photo",
        "outerwear_garment_photo",
        "full_body_garment_photo",
    ):
        assert slot_role in workflow_source


def test_try_on_workspace_polls_backend_until_analysis_and_generation_are_ready() -> None:
    workflow_source = Path("apps/web/src/features/workspace/try-on-workflow.tsx").read_text(encoding="utf-8")

    assert "pollTryOnJobStatus" in workflow_source
    assert "onStatus(currentStatus)" in workflow_source
    assert 'terminalStatuses.includes(currentStatus.status)' in workflow_source
    assert '["analysis_ready", "completed", "failed"]' in workflow_source
    assert '["completed", "failed"]' in workflow_source
    assert "getTryOnPreGenerationAnalysis(created.job_id)" in workflow_source
    assert "continueTryOnGeneration(createdJobId)" in workflow_source
