from __future__ import annotations

from types import SimpleNamespace


class _ProviderRuntime:
    def __init__(self, image_editing) -> None:
        self.image_editing = image_editing
        self.agent_runtime = object()


class _ImageEditingProvider:
    provider_name = "google_genai_image_editing"

    def __init__(self, *, storage) -> None:
        self._storage = storage
        self.requests = []

    def edit(self, request):
        from src.domain.provider_models import ImageEditingResult

        self.requests.append(request)
        output_key = "provider-artifacts/image-editing/repair-workflow/edited.png"
        self._storage.put_bytes(
            object_key=output_key,
            payload=b"repaired-image-bytes" * 5000,
            content_type=request.output_mime_type,
        )
        return ImageEditingResult(
            task=request.task,
            source_object_key=request.source_object_key,
            output_object_key=output_key,
            output_mime_type=request.output_mime_type,
            provider=self.provider_name,
        )


def test_repair_workflow_acceptance_runs_repair_and_second_quality_verifier(tmp_path, monkeypatch) -> None:
    from scripts import repair_workflow_live_acceptance
    from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage

    case_dir = tmp_path / "minor_background_artifact"
    case_dir.mkdir()
    (case_dir / "generated_result.png").write_bytes(b"source-image-bytes" * 1000)
    (case_dir / "human_source.png").write_bytes(b"human-image-bytes" * 1000)
    (case_dir / "garment_source.png").write_bytes(b"garment-image-bytes" * 1000)
    output = tmp_path / "repair-workflow.jsonl"
    storage = InMemoryObjectStorage()
    image_editing_provider = _ImageEditingProvider(storage=storage)
    created_planners = []

    monkeypatch.setattr(
        repair_workflow_live_acceptance,
        "_load_settings",
        lambda env_file: SimpleNamespace(image_editing_provider="google_genai"),
    )
    monkeypatch.setattr(
        repair_workflow_live_acceptance,
        "_build_object_storage",
        lambda settings: storage,
    )
    monkeypatch.setattr(
        repair_workflow_live_acceptance,
        "build_provider_runtime",
        lambda settings, object_storage: _ProviderRuntime(image_editing_provider),
    )

    class _RepairAgentPlanner:
        def __init__(self, **kwargs) -> None:
            created_planners.append(kwargs)

        async def create_plan(self, *, job_id, result, quality_report):
            from src.adk_agents.repair_agent.contracts import RepairInstructionContract, RepairRegionInstruction

            return RepairInstructionContract(
                repair_scope="local",
                target_issues=["background"],
                editing_instructions=["Remove the local background artifact only."],
                confidence=0.9,
                limitations=[],
                region_instructions=[
                    RepairRegionInstruction(
                        region="upper right background",
                        instruction="Clean the local background artifact.",
                        preserve=["face", "identity", "pose", "garment"],
                    )
                ],
            )

    monkeypatch.setattr(repair_workflow_live_acceptance, "TryOnRepairAgentPlanner", _RepairAgentPlanner)

    exit_code = repair_workflow_live_acceptance.main(
        [
            "--case-dir",
            str(case_dir),
            "--output",
            str(output),
            "--require-pass",
        ]
    )

    assert exit_code == 0
    rows = output.read_text(encoding="utf-8").splitlines()
    assert '"type": "summary"' in rows[-1]
    assert '"passed": true' in rows[-1]
    assert '"second_quality_verdict": "pass"' in rows[-1]
    assert '"provider": "google_genai_image_editing"' in rows[-1]
    assert created_planners
    assert image_editing_provider.requests
    assert "Repair Agent approved local plan" in image_editing_provider.requests[0].prompt
    assert "Clean the local background artifact" in image_editing_provider.requests[0].prompt
