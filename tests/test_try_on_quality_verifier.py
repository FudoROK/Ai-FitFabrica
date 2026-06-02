from __future__ import annotations

import pytest

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStoredInput,
    TryOnUploadRole,
    TryOnWorkflowType,
)


def _generated_result(*, object_key: str | None) -> TryOnResult:
    result_image = TryOnResultImage(
        kind="generated_artifact",
        url="memory://fitfabrica/tenants/public/try-on/job-1/result_image/result.png",
        alt="Try-On result",
    )
    result_image._artifact_object_key = object_key
    return TryOnResult(
        job_id="job-1",
        workflow_type=TryOnWorkflowType.TRY_ON,
        result_image=result_image,
        quality_report=TryOnQualityReport(
            verdict="pass",
            confidence=0.8,
            checks=[
                TryOnQualityCheck(
                    name="generation_complete",
                    status="passed",
                    confidence=0.8,
                    message="Generation completed.",
                )
            ],
            limitations=[],
        ),
        stylist_note="Generated result.",
        input_metadata=[],
    )


@pytest.mark.asyncio
async def test_deterministic_try_on_quality_verifier_passes_vertex_generated_artifact() -> None:
    storage = InMemoryObjectStorage()
    object_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=object_key, payload=b"x" * 128, content_type="image/png")
    verifier = DeterministicTryOnQualityVerifier(object_storage=storage)

    report = await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=[
            TryOnInputMetadata(
                role=TryOnUploadRole.HUMAN_PHOTO,
                filename="human.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnInputMetadata(
                role=TryOnUploadRole.GARMENT_PHOTO,
                filename="garment.jpg",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            ),
        ],
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
        result=_generated_result(object_key=object_key),
    )

    assert report.verdict == "pass"
    assert any(check.name == "generated_artifact_non_empty" and check.status == "passed" for check in report.checks)


@pytest.mark.asyncio
async def test_deterministic_try_on_quality_verifier_rejects_missing_artifact_reference() -> None:
    verifier = DeterministicTryOnQualityVerifier(object_storage=InMemoryObjectStorage())

    report = await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=[],
        stored_inputs=[],
        result=_generated_result(object_key=None),
    )

    assert report.verdict == "reject"
    assert any(check.name == "generated_artifact_reference" and check.status == "failed" for check in report.checks)


@pytest.mark.asyncio
async def test_deterministic_try_on_quality_verifier_recommends_repair_for_tiny_artifact() -> None:
    storage = InMemoryObjectStorage()
    object_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=object_key, payload=b"tiny", content_type="image/png")
    verifier = DeterministicTryOnQualityVerifier(object_storage=storage)

    report = await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=[
            TryOnInputMetadata(
                role=TryOnUploadRole.HUMAN_PHOTO,
                filename="human.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            ),
            TryOnInputMetadata(
                role=TryOnUploadRole.GARMENT_PHOTO,
                filename="garment.jpg",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            ),
        ],
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
        result=_generated_result(object_key=object_key),
    )

    assert report.verdict == "repair_recommended"
    assert any(check.name == "generated_artifact_size_sanity" and check.status == "warning" for check in report.checks)
