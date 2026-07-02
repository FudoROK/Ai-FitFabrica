from __future__ import annotations

import pytest

from src.adapters.agents.human_identity_analysis import HumanIdentityAnalysisAdapter
from src.domain.agent_runtime import (
    AgentInvocationEnvelope,
    AgentInvocationErrorDetail,
    AgentRuntimeStatus,
    AgentValidationStatus,
)
from src.domain.try_on import TryOnHumanIdentityVerdict, TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.human_identity_policy import HumanIdentityContinuationPolicy
from src.use_cases.try_on.human_identity_errors import HumanIdentityAnalysisFailure


class _InvocationServiceStub:
    def __init__(self, envelope: AgentInvocationEnvelope) -> None:
        self.envelope = envelope
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append((request, output_contract))
        return self.envelope


def _stored_human() -> TryOnStoredInput:
    return TryOnStoredInput(
        role=TryOnUploadRole.HUMAN_PHOTO,
        storage_backend="s3",
        uri="s3://bucket/public/job/human.png",
        bucket_name="bucket",
        object_key="public/job/human.png",
        object_name="public/job/human.png",
        content_type="image/png",
        size_bytes=32,
        sha256="a" * 64,
    )


def _successful_envelope() -> AgentInvocationEnvelope:
    return AgentInvocationEnvelope(
        invocation_id="invocation-1",
        trace_id="try_on_1",
        agent_name="human_identity_agent",
        prompt_version="human_identity.v1",
        contract_version="human_identity.contract.v1",
        status=AgentRuntimeStatus.SUCCEEDED,
        validation_status=AgentValidationStatus.PASSED,
        output={
            "face_visibility": "fully_visible",
            "pose_summary": "Front-facing standing pose.",
            "body_region_visibility": ["face", "torso", "arms"],
            "subject_count": 1,
            "crop_quality": "full_body",
            "try_on_body_coverage": "sufficient",
            "occlusion_risk": "low",
            "required_regions_missing": [],
            "preservation_targets": [
                {"attribute_name": "face", "preservation_reason": "Visible source identity must remain unchanged."}
            ],
            "confidence": 0.94,
            "limitations": [],
            "evidence": [
                {
                    "source_type": "artifact",
                    "source_ref": "public/job/human.png",
                    "observation": "Face and torso are visible.",
                    "confidence": 0.96,
                }
            ],
            "uncertainty_level": "low",
            "unknowns": [],
        },
        provider="fake",
        model="fake-model",
        latency_ms=10,
        confidence=0.94,
    )


@pytest.mark.anyio
async def test_human_identity_adapter_returns_policy_evaluated_snapshot() -> None:
    invocation_service = _InvocationServiceStub(_successful_envelope())
    adapter = HumanIdentityAnalysisAdapter(
        invocation_service=invocation_service,
        policy=HumanIdentityContinuationPolicy(minimum_confidence=0.8),
        timeout_seconds=30,
        preferred_model="gemini-test",
    )

    analysis = await adapter.analyze(job_id="try_on_1", stored_inputs=[_stored_human()])

    request, output_contract = invocation_service.requests[0]
    assert request.input_payload == {
        "human_photo_object_key": "public/job/human.png",
        "requested_checks": ["face_visibility", "pose", "body_regions", "lighting", "background"],
    }
    assert len(request.artifact_references) == 1
    artifact = request.artifact_references[0]
    assert artifact.purpose == "human_photo"
    assert artifact.object_key == "public/job/human.png"
    assert artifact.content_type == "image/png"
    assert artifact.size_bytes == 32
    assert artifact.sha256 == "a" * 64
    assert output_contract.__name__ == "HumanIdentityContract"
    assert analysis.verdict == TryOnHumanIdentityVerdict.ALLOWED
    assert analysis.invocation_id == "invocation-1"
    assert analysis.face_visibility == "fully_visible"
    assert analysis.subject_count == 1
    assert analysis.crop_quality == "full_body"
    assert analysis.try_on_body_coverage == "sufficient"
    assert analysis.occlusion_risk == "low"
    assert analysis.required_regions_missing == []


@pytest.mark.anyio
async def test_human_identity_adapter_maps_invocation_failure_to_safe_failure() -> None:
    envelope = AgentInvocationEnvelope(
        invocation_id="invocation-2",
        trace_id="try_on_2",
        agent_name="human_identity_agent",
        prompt_version="human_identity.v1",
        contract_version="human_identity.contract.v1",
        status=AgentRuntimeStatus.FAILED,
        validation_status=AgentValidationStatus.NOT_RUN,
        error=AgentInvocationErrorDetail(code="timeout", message="Agent invocation timed out.", retriable=True),
    )
    adapter = HumanIdentityAnalysisAdapter(
        invocation_service=_InvocationServiceStub(envelope),
        policy=HumanIdentityContinuationPolicy(minimum_confidence=0.8),
        timeout_seconds=30,
        preferred_model=None,
    )

    with pytest.raises(HumanIdentityAnalysisFailure, match="Human Identity analysis failed") as exc_info:
        await adapter.analyze(job_id="try_on_2", stored_inputs=[_stored_human()])

    assert exc_info.value.safe_code == "timeout"
