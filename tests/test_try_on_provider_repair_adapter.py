from __future__ import annotations

import pytest

from src.adapters.ai.image_editing_stub import StubImageEditingProvider
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.provider_repair_adapter import ProviderRuntimeTryOnRepairAdapter
from src.adk_agents.repair_agent.contracts import RepairInstructionContract, RepairRegionInstruction
from src.domain.provider_models import ImageEditingResult
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStoredInput,
    TryOnUploadRole,
    TryOnWorkflowType,
)


def _result(object_key: str) -> TryOnResult:
    image = TryOnResultImage(
        kind="generated_artifact",
        url=f"memory://{object_key}",
        alt="Generated Try-On result",
    )
    image._artifact_object_key = object_key
    return TryOnResult(
        job_id="job-1",
        workflow_type=TryOnWorkflowType.TRY_ON,
        result_image=image,
        quality_report=TryOnQualityReport(
            verdict="repair_recommended",
            confidence=0.6,
            checks=[
                TryOnQualityCheck(
                    name="generated_artifact_size_sanity",
                    status="warning",
                    confidence=0.6,
                    message="Artifact is too small.",
                )
            ],
            limitations=["Repair required."],
        ),
        stylist_note="Original result.",
        input_metadata=[],
    )


@pytest.mark.asyncio
async def test_provider_runtime_repair_adapter_creates_backend_owned_repaired_artifact() -> None:
    storage = InMemoryObjectStorage()
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"tiny", content_type="image/png")
    adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=StubImageEditingProvider(),
        object_storage=storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
    )

    repaired = await adapter.repair(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        stored_inputs=[
            TryOnStoredInput(
                role=TryOnUploadRole.HUMAN_PHOTO,
                storage_backend="in_memory",
                uri="memory://fitfabrica/human",
                object_key="fitfabrica/human",
                object_name="fitfabrica/human",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnStoredInput(
                role=TryOnUploadRole.GARMENT_PHOTO,
                storage_backend="in_memory",
                uri="memory://fitfabrica/garment",
                object_key="fitfabrica/garment",
                object_name="fitfabrica/garment",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            ),
        ],
        result=_result(source_key),
        quality_report=_result(source_key).quality_report,
    )

    assert repaired.result_image._artifact_object_key is not None
    assert repaired.result_image._artifact_object_key.endswith("/repair_image/repair.png")
    assert repaired.result_image.url.startswith("memory://fitfabrica/tenants/public/try-on/job-1/repair_image/")
    stored_bytes = storage.get_bytes(repaired.result_image._artifact_object_key)
    assert stored_bytes.startswith(b"try_on_provider_repair:stub_image_editing:edited/repair_try_on_result/")


@pytest.mark.asyncio
async def test_provider_runtime_repair_adapter_blocks_stub_provider_for_real_generation() -> None:
    storage = InMemoryObjectStorage()
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"real-image-bytes", content_type="image/png")
    adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=StubImageEditingProvider(),
        object_storage=storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
    )

    repaired = await adapter.repair(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        stored_inputs=[],
        result=_result(source_key),
        quality_report=_result(source_key).quality_report,
    )

    assert repaired.result_image._artifact_object_key == source_key
    assert repaired.quality_report.verdict == "reject"
    assert any(check.name == "repair_provider_not_production_ready" for check in repaired.quality_report.checks)


class _RecordingImageEditingProvider(StubImageEditingProvider):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def edit(self, request):
        self.calls += 1
        return super().edit(request)


class _PersistingImageEditingProvider:
    provider_name = "persisting_image_editing"

    def __init__(self, *, storage: InMemoryObjectStorage) -> None:
        self._storage = storage
        self.requests = []

    def edit(self, request):
        self.requests.append(request)
        output_key = "provider-artifacts/image-editing/repair_try_on_result/edited.webp"
        self._storage.put_bytes(
            object_key=output_key,
            payload=b"real-edited-image-bytes",
            content_type=request.output_mime_type,
        )
        return ImageEditingResult(
            task=request.task,
            source_object_key=request.source_object_key,
            output_object_key=output_key,
            output_mime_type=request.output_mime_type,
            provider=self.provider_name,
        )


class _LocalRepairInstructionPlanner:
    def __init__(self) -> None:
        self.calls = 0

    async def create_plan(self, *, job_id, result, quality_report):
        self.calls += 1
        return RepairInstructionContract(
            repair_scope="local",
            target_issues=["background"],
            editing_instructions=["Remove only the orange background stain."],
            confidence=0.91,
            region_instructions=[
                RepairRegionInstruction(
                    region="upper right background",
                    instruction="Clean the orange stain without changing the person or garment.",
                    preserve=["face", "identity", "pose", "garment"],
                )
            ],
        )


class _UnsafeRepairInstructionPlanner:
    def __init__(self) -> None:
        self.calls = 0

    async def create_plan(self, *, job_id, result, quality_report):
        self.calls += 1
        return RepairInstructionContract(
            repair_scope="unsafe",
            target_issues=["face"],
            editing_instructions=[],
            confidence=0.97,
            limitations=["Face identity changes cannot be repaired locally."],
        )


class _FailingRepairInstructionPlanner:
    async def create_plan(self, *, job_id, result, quality_report):
        raise RuntimeError("planner unavailable")


@pytest.mark.asyncio
async def test_provider_runtime_repair_adapter_persists_provider_edited_bytes() -> None:
    storage = InMemoryObjectStorage()
    provider = _PersistingImageEditingProvider(storage=storage)
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"tiny", content_type="image/png")
    adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=provider,
        object_storage=storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
    )

    repaired = await adapter.repair(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        stored_inputs=[
            TryOnStoredInput(
                role=TryOnUploadRole.HUMAN_PHOTO,
                storage_backend="in_memory",
                uri="memory://fitfabrica/human",
                object_key="fitfabrica/human",
                object_name="fitfabrica/human",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnStoredInput(
                role=TryOnUploadRole.GARMENT_PHOTO,
                storage_backend="in_memory",
                uri="memory://fitfabrica/garment",
                object_key="fitfabrica/garment",
                object_name="fitfabrica/garment",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            ),
        ],
        result=_result(source_key),
        quality_report=_result(source_key).quality_report,
    )

    assert repaired.result_image._artifact_object_key is not None
    assert storage.get_bytes(repaired.result_image._artifact_object_key) == b"real-edited-image-bytes"
    assert provider.requests[0].source_object_key == source_key
    assert provider.requests[0].reference_object_keys == ["fitfabrica/human", "fitfabrica/garment"]


@pytest.mark.asyncio
async def test_provider_runtime_repair_adapter_uses_repair_agent_plan_in_edit_prompt() -> None:
    storage = InMemoryObjectStorage()
    provider = _PersistingImageEditingProvider(storage=storage)
    planner = _LocalRepairInstructionPlanner()
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"tiny", content_type="image/png")
    adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=provider,
        object_storage=storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
        repair_instruction_planner=planner,
    )

    await adapter.repair(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        stored_inputs=[],
        result=_result(source_key),
        quality_report=_result(source_key).quality_report,
    )

    assert planner.calls == 1
    assert "Repair Agent approved local plan" in provider.requests[0].prompt
    assert "Clean the orange stain" in provider.requests[0].prompt
    assert "preserve: face, identity, pose, garment" in provider.requests[0].prompt


@pytest.mark.asyncio
async def test_provider_runtime_repair_adapter_blocks_unsafe_repair_agent_plan_without_calling_provider() -> None:
    storage = InMemoryObjectStorage()
    provider = _PersistingImageEditingProvider(storage=storage)
    planner = _UnsafeRepairInstructionPlanner()
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"tiny", content_type="image/png")
    adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=provider,
        object_storage=storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
        repair_instruction_planner=planner,
    )

    repaired = await adapter.repair(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        stored_inputs=[],
        result=_result(source_key),
        quality_report=_result(source_key).quality_report,
    )

    assert planner.calls == 1
    assert provider.requests == []
    assert repaired.result_image._artifact_object_key == source_key
    assert repaired.quality_report.verdict == "reject"
    assert any(check.name == "repair_agent_blocked" for check in repaired.quality_report.checks)


@pytest.mark.asyncio
async def test_provider_runtime_repair_adapter_fails_closed_when_repair_agent_planner_errors() -> None:
    storage = InMemoryObjectStorage()
    provider = _PersistingImageEditingProvider(storage=storage)
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"tiny", content_type="image/png")
    adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=provider,
        object_storage=storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
        repair_instruction_planner=_FailingRepairInstructionPlanner(),
    )

    repaired = await adapter.repair(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        stored_inputs=[],
        result=_result(source_key),
        quality_report=_result(source_key).quality_report,
    )

    assert provider.requests == []
    assert repaired.result_image._artifact_object_key == source_key
    assert repaired.quality_report.verdict == "reject"
    assert any(
        check.name == "repair_agent_unavailable" and "planner unavailable" in check.message
        for check in repaired.quality_report.checks
    )


@pytest.mark.asyncio
async def test_provider_runtime_repair_adapter_refuses_unsafe_repair_without_calling_provider() -> None:
    storage = InMemoryObjectStorage()
    provider = _RecordingImageEditingProvider()
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"tiny", content_type="image/png")
    adapter = ProviderRuntimeTryOnRepairAdapter(
        image_editing_provider=provider,
        object_storage=storage,
        tenant_id="public",
        root_prefix="fitfabrica",
        signed_url_ttl_seconds=900,
    )
    unsafe_report = TryOnQualityReport(
        verdict="repair_recommended",
        confidence=0.8,
        checks=[
            TryOnQualityCheck(
                name="face_preservation",
                status="failed",
                confidence=0.9,
                message="Face changed.",
            )
        ],
        limitations=["Not locally repairable."],
    )

    repaired = await adapter.repair(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
        stored_inputs=[],
        result=_result(source_key),
        quality_report=unsafe_report,
    )

    assert provider.calls == 0
    assert repaired.result_image._artifact_object_key == source_key
    assert any(check.name == "repair_policy_blocked" for check in repaired.quality_report.checks)
