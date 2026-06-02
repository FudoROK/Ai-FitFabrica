from __future__ import annotations

import pytest

from src.adapters.try_on.model_backed_stylist import ModelBackedTryOnStylist
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
    """Structured reasoning stub for stylist tests."""

    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload
        self.requests = []

    def generate_structured(self, request):
        self.requests.append(request)
        return StructuredReasoningResult(
            task=request.task,
            payload=self.payload,
            provider="stub",
            model="stub-model",
        )


def _result() -> TryOnResult:
    return TryOnResult(
        job_id="job-1",
        workflow_type=TryOnWorkflowType.TRY_ON,
        result_image=TryOnResultImage(
            kind="generated_artifact",
            url="memory://fitfabrica/result",
            alt="Generated Try-On result",
        ),
        quality_report=TryOnQualityReport(verdict="pass", confidence=0.9, checks=[], limitations=[]),
        stylist_note="Generator note that should be replaced.",
        input_metadata=[],
    )


@pytest.mark.asyncio
async def test_model_backed_stylist_returns_structured_note() -> None:
    stylist = ModelBackedTryOnStylist(
        structured_reasoning_provider=_StructuredReasoningStub(
            {"note": "Модельный stylist backend подготовил итоговую fashion-подсказку."}
        )
    )

    note = await stylist.generate_note(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=[
            TryOnInputMetadata(
                role=TryOnUploadRole.HUMAN_PHOTO,
                filename="human.jpg",
                content_type="image/jpeg",
                size_bytes=10,
                sha256="a" * 64,
            )
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
            )
        ],
        result=_result(),
    )

    assert note == "Модельный stylist backend подготовил итоговую fashion-подсказку."
