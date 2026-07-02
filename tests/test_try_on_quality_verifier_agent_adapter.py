from __future__ import annotations

from hashlib import sha256
from io import BytesIO

import pytest
from PIL import Image

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from src.adapters.try_on.quality_verifier_agent_adapter import TryOnQualityVerifierAgentAdapter
from src.domain.agent_runtime import (
    AgentInvocationEnvelope,
    AgentInvocationErrorDetail,
    AgentRuntimeStatus,
    AgentValidationStatus,
)
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


class _InvocationServiceStub:
    def __init__(self, output: dict[str, object]) -> None:
        self.output = output
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append(request)
        return AgentInvocationEnvelope(
            invocation_id="quality-agent-invocation-1",
            trace_id=request.trace_id,
            agent_name=request.agent_name,
            prompt_version=request.prompt_version,
            contract_version=request.contract_version,
            status=AgentRuntimeStatus.SUCCEEDED,
            validation_status=AgentValidationStatus.PASSED,
            output=self.output,
            provider="stub",
            model="quality-verifier-stub",
            confidence=float(self.output["confidence"]),
        )


class _FailedInvocationServiceStub:
    def __init__(self, message: str) -> None:
        self.message = message
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append(request)
        return AgentInvocationEnvelope(
            invocation_id="quality-agent-invocation-failed",
            trace_id=request.trace_id,
            agent_name=request.agent_name,
            prompt_version=request.prompt_version,
            contract_version=request.contract_version,
            status=AgentRuntimeStatus.FAILED,
            validation_status=AgentValidationStatus.FAILED,
            output=None,
            error=AgentInvocationErrorDetail(
                code="provider_invalid_image",
                message=self.message,
                retriable=False,
            ),
        )


@pytest.mark.asyncio
async def test_quality_verifier_agent_adapter_rejects_blocking_extra_hand_defect() -> None:
    storage, result, input_metadata, stored_inputs = _quality_context()
    invocation_service = _InvocationServiceStub(
        {
            "verdict": "reject",
            "summary": "Generated image contains an extra visible hand near the waist.",
            "blocking_issues": ["extra hand near waist"],
            "repair_targets": [],
            "confidence": 0.91,
            "limitations": [],
            "defects": [
                {
                    "defect_type": "hands",
                    "region": "waist / right side",
                    "severity": "blocking",
                    "evidence": "A second hand-like shape is visible where only one hand should appear.",
                    "repairable": False,
                    "confidence": 0.91,
                }
            ],
            "category_scores": [
                {
                    "category": "anatomy",
                    "score": 0.21,
                    "evidence": "Hand anatomy is inconsistent with the source person.",
                }
            ],
            "evidence": [],
            "uncertainty_level": "low",
        }
    )
    verifier = TryOnQualityVerifierAgentAdapter(
        baseline_verifier=DeterministicTryOnQualityVerifier(object_storage=storage),
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=120.0,
        preferred_model="quality-verifier-stub",
    )

    report = await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        result=result,
    )

    assert report.verdict == "reject"
    assert any(
        check.name == "visual_defect_hands" and check.status == "failed" and "extra visible hand" in check.message
        for check in report.checks
    )


@pytest.mark.asyncio
async def test_quality_verifier_agent_adapter_routes_wear_control_violation_to_repair() -> None:
    storage, result, input_metadata, stored_inputs = _quality_context()
    invocation_service = _InvocationServiceStub(
        {
            "verdict": "repair_recommended",
            "summary": "The selected untucked styling is partially violated.",
            "blocking_issues": [],
            "repair_targets": ["shirt hem visibility"],
            "confidence": 0.86,
            "limitations": [],
            "defects": [
                {
                    "defect_type": "wear_control",
                    "region": "waist",
                    "severity": "minor",
                    "evidence": "The shirt hem is partly tucked into the jeans.",
                    "repairable": True,
                    "confidence": 0.86,
                }
            ],
            "category_scores": [
                {
                    "category": "wear_control_match",
                    "score": 0.64,
                    "evidence": "Requested untucked styling is not fully preserved.",
                }
            ],
            "evidence": [],
            "uncertainty_level": "low",
        }
    )
    verifier = TryOnQualityVerifierAgentAdapter(
        baseline_verifier=DeterministicTryOnQualityVerifier(object_storage=storage),
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=120.0,
        preferred_model="quality-verifier-stub",
    )

    report = await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        result=result,
    )

    assert report.verdict == "repair_recommended"
    assert any(check.name == "visual_defect_wear_control" and check.status == "warning" for check in report.checks)
    assert any(check.name == "visual_category_wear_control_match" for check in report.checks)


@pytest.mark.asyncio
async def test_quality_verifier_agent_adapter_sends_source_and_result_artifacts() -> None:
    storage, result, input_metadata, stored_inputs = _quality_context()
    invocation_service = _InvocationServiceStub(
        {
            "verdict": "pass",
            "summary": "No blocking visual defects were detected.",
            "blocking_issues": [],
            "repair_targets": [],
            "confidence": 0.88,
            "limitations": [],
            "defects": [],
            "category_scores": [],
            "evidence": [],
            "uncertainty_level": "low",
        }
    )
    verifier = TryOnQualityVerifierAgentAdapter(
        baseline_verifier=DeterministicTryOnQualityVerifier(object_storage=storage),
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=120.0,
        preferred_model="quality-verifier-stub",
    )

    await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        result=result,
    )

    request = invocation_service.requests[0]
    artifact_purposes = {artifact.purpose for artifact in request.artifact_references}
    assert artifact_purposes == {"human_photo", "garment_photo", "generated_result"}
    generated_reference = next(artifact for artifact in request.artifact_references if artifact.purpose == "generated_result")
    assert generated_reference.size_bytes == 128
    assert generated_reference.sha256 == sha256(b"x" * 128).hexdigest()
    assert request.input_payload["generated_image_object_key"] == "fitfabrica/result.png"


@pytest.mark.asyncio
async def test_quality_verifier_agent_adapter_normalizes_large_generated_png_before_visual_agent() -> None:
    storage, result, input_metadata, stored_inputs = _quality_context(
        generated_payload=_png_bytes(width=2400, height=3600),
    )
    invocation_service = _InvocationServiceStub(
        {
            "verdict": "pass",
            "summary": "No blocking visual defects were detected.",
            "blocking_issues": [],
            "repair_targets": [],
            "confidence": 0.88,
            "limitations": [],
            "defects": [],
            "category_scores": [],
            "evidence": [],
            "uncertainty_level": "low",
        }
    )
    verifier = TryOnQualityVerifierAgentAdapter(
        baseline_verifier=DeterministicTryOnQualityVerifier(object_storage=storage),
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=120.0,
        preferred_model="quality-verifier-stub",
    )

    await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        result=result,
    )

    request = invocation_service.requests[0]
    generated_reference = next(artifact for artifact in request.artifact_references if artifact.purpose == "generated_result")
    normalized_payload = storage.get_bytes(generated_reference.object_key)
    with Image.open(BytesIO(normalized_payload)) as image:
        assert image.format == "JPEG"
        assert max(image.size) <= 1600
    assert generated_reference.content_type == "image/jpeg"
    assert generated_reference.object_key.endswith("/quality_verifier/generated_result.jpg")
    assert generated_reference.size_bytes == len(normalized_payload)
    assert generated_reference.sha256 == sha256(normalized_payload).hexdigest()
    assert request.input_payload["generated_image_object_key"] == generated_reference.object_key


@pytest.mark.asyncio
async def test_quality_verifier_agent_adapter_rejects_when_visual_agent_cannot_read_result_image() -> None:
    storage, result, input_metadata, stored_inputs = _quality_context()
    invocation_service = _FailedInvocationServiceStub("Provided image is not valid.")
    verifier = TryOnQualityVerifierAgentAdapter(
        baseline_verifier=DeterministicTryOnQualityVerifier(object_storage=storage),
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=120.0,
        preferred_model="quality-verifier-stub",
    )

    report = await verifier.verify(
        job_id="job-1",
        generation_mode=TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON,
        input_metadata=input_metadata,
        stored_inputs=stored_inputs,
        result=result,
    )

    assert report.verdict == "reject"
    assert any(
        check.name == "quality_verifier_agent_unavailable"
        and check.status == "failed"
        and "Provided image is not valid" in check.message
        for check in report.checks
    )


def _quality_context(*, generated_payload: bytes = b"x" * 128):
    storage = InMemoryObjectStorage()
    storage.put_bytes(object_key="fitfabrica/result.png", payload=generated_payload, content_type="image/png")
    result_image = TryOnResultImage(
        kind="generated_artifact",
        url="memory://fitfabrica/result.png",
        alt="Generated Try-On result",
    )
    result_image._artifact_object_key = "fitfabrica/result.png"
    result = TryOnResult(
        job_id="job-1",
        workflow_type=TryOnWorkflowType.TRY_ON,
        result_image=result_image,
        quality_report=TryOnQualityReport(verdict="pass", confidence=0.8, checks=[], limitations=[]),
        stylist_note="Generated result.",
        input_metadata=[],
    )
    input_metadata = [
        _metadata(TryOnUploadRole.HUMAN_PHOTO),
        _metadata(TryOnUploadRole.GARMENT_PHOTO),
    ]
    stored_inputs = [
        _stored(TryOnUploadRole.HUMAN_PHOTO, "fitfabrica/human.jpg"),
        _stored(TryOnUploadRole.GARMENT_PHOTO, "fitfabrica/garment.png"),
    ]
    return storage, result, input_metadata, stored_inputs


def _png_bytes(*, width: int, height: int) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (width, height), color=(220, 220, 220)).save(buffer, format="PNG")
    return buffer.getvalue()


def _metadata(role: TryOnUploadRole) -> TryOnInputMetadata:
    return TryOnInputMetadata(
        role=role,
        filename=f"{role.value}.jpg",
        content_type="image/jpeg",
        size_bytes=128,
        sha256="a" * 64,
    )


def _stored(role: TryOnUploadRole, object_key: str) -> TryOnStoredInput:
    return TryOnStoredInput(
        role=role,
        storage_backend="in_memory",
        uri=f"memory://{object_key}",
        object_key=object_key,
        object_name=object_key,
        content_type="image/jpeg" if role == TryOnUploadRole.HUMAN_PHOTO else "image/png",
        size_bytes=128,
        sha256="a" * 64,
    )
