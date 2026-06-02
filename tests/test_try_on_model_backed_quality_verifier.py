from __future__ import annotations

import pytest

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from src.adapters.try_on.model_backed_quality_verifier import ModelBackedTryOnQualityVerifier
from src.domain.provider_models import StructuredReasoningResult
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStoredInput,
    TryOnUploadRole,
    TryOnWorkflowType,
)


class _StructuredReasoningStub:
    """Structured reasoning stub for quality-verifier tests."""

    def __init__(self, verdict: str) -> None:
        self.verdict = verdict
        self.requests = []

    def generate_structured(self, request):
        self.requests.append(request)
        return StructuredReasoningResult(
            task=request.task,
            payload={
                "verdict": self.verdict,
                "confidence": 0.83,
                "summary": "Model-backed verifier produced a structured decision.",
                "limitations": ["Model-backed verifier used backend facts only."],
            },
            provider="stub",
            model="stub-model",
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
        quality_report=TryOnQualityReport(verdict="pass", confidence=0.8, checks=[], limitations=[]),
        stylist_note="Generated result.",
        input_metadata=[],
    )


@pytest.mark.asyncio
async def test_model_backed_quality_verifier_overrides_baseline_with_structured_decision() -> None:
    storage = InMemoryObjectStorage()
    object_key = "fitfabrica/tenants/public/try-on/job-1/result_image/result.png"
    storage.put_bytes(object_key=object_key, payload=b"x" * 128, content_type="image/png")
    verifier = ModelBackedTryOnQualityVerifier(
        baseline_verifier=DeterministicTryOnQualityVerifier(object_storage=storage),
        structured_reasoning_provider=_StructuredReasoningStub("repair_recommended"),
    )

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
        result=_result(object_key),
    )

    assert report.verdict == "repair_recommended"
    assert any(check.name == "model_backed_verdict" for check in report.checks)
