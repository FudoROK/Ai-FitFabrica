from __future__ import annotations

import pytest

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.deterministic_repair_adapter import DeterministicTryOnRepairAdapter
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
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
async def test_deterministic_repair_adapter_creates_repaired_artifact_variant() -> None:
    storage = InMemoryObjectStorage()
    source_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=source_key, payload=b"tiny", content_type="image/png")
    adapter = DeterministicTryOnRepairAdapter(
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

    assert repaired.result_image._artifact_object_key is not None
    assert repaired.result_image._artifact_object_key.endswith("/repair_image/repair.png")
    assert repaired.result_image.url.startswith("memory://fitfabrica/tenants/public/try-on/job-1/repair_image/")
    assert len(storage.get_bytes(repaired.result_image._artifact_object_key)) >= 64
