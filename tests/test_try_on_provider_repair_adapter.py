from __future__ import annotations

import pytest

from src.adapters.ai.image_editing_stub import StubImageEditingProvider
from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.provider_repair_adapter import ProviderRuntimeTryOnRepairAdapter
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
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
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
    assert repaired.result_image._artifact_object_key.endswith("/repair_image/repair.webp")
    assert repaired.result_image.url.startswith("memory://fitfabrica/tenants/public/try-on/job-1/repair_image/")
    stored_bytes = storage.get_bytes(repaired.result_image._artifact_object_key)
    assert stored_bytes.startswith(b"try_on_provider_repair:stub_image_editing:edited/repair_try_on_result/")
