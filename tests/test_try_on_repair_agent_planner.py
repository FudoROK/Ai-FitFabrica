from __future__ import annotations

import pytest

from src.adapters.storage.in_memory_object_storage import InMemoryObjectStorage
from src.adapters.try_on.repair_agent_planner import TryOnRepairAgentPlanner
from src.domain.agent_runtime import (
    AgentInvocationEnvelope,
    AgentInvocationErrorDetail,
    AgentRuntimeStatus,
    AgentValidationStatus,
)
from src.domain.try_on import (
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnWorkflowType,
)


class _InvocationServiceStub:
    def __init__(self, output: dict[str, object]) -> None:
        self.output = output
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append(request)
        return AgentInvocationEnvelope(
            invocation_id="repair-agent-invocation-1",
            trace_id=request.trace_id,
            agent_name=request.agent_name,
            prompt_version=request.prompt_version,
            contract_version=request.contract_version,
            status=AgentRuntimeStatus.SUCCEEDED,
            validation_status=AgentValidationStatus.PASSED,
            output=self.output,
            provider="stub",
            model="repair-agent-stub",
            confidence=float(self.output["confidence"]),
        )


class _FailedInvocationServiceStub:
    def __init__(self, message: str) -> None:
        self.message = message
        self.requests = []

    async def invoke(self, *, request, output_contract):
        self.requests.append(request)
        return AgentInvocationEnvelope(
            invocation_id="repair-agent-invocation-failed",
            trace_id=request.trace_id,
            agent_name=request.agent_name,
            prompt_version=request.prompt_version,
            contract_version=request.contract_version,
            status=AgentRuntimeStatus.FAILED,
            validation_status=AgentValidationStatus.FAILED,
            output=None,
            error=AgentInvocationErrorDetail(
                code="invalid_output",
                message=self.message,
                retriable=False,
            ),
        )


@pytest.mark.asyncio
async def test_repair_agent_planner_sends_generated_artifact_and_approved_defects() -> None:
    storage, result, report = _repair_context()
    invocation_service = _InvocationServiceStub(
        {
            "repair_scope": "local",
            "target_issues": ["background"],
            "editing_instructions": ["Remove only the orange background stain."],
            "confidence": 0.9,
            "limitations": [],
            "region_instructions": [
                {
                    "region": "upper right background",
                    "instruction": "Clean the orange stain without changing the person or garment.",
                    "preserve": ["face", "identity", "pose", "garment"],
                }
            ],
            "evidence": [],
            "uncertainty_level": "low",
        }
    )
    planner = TryOnRepairAgentPlanner(
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=90.0,
        preferred_model="repair-agent-stub",
    )

    plan = await planner.create_plan(job_id="job-1", result=result, quality_report=report)

    assert plan.repair_scope == "local"
    request = invocation_service.requests[0]
    assert request.agent_name == "repair_agent"
    assert request.trace_id == "job-1"
    assert request.preferred_model == "repair-agent-stub"
    assert request.input_payload["generated_image_object_key"] == "fitfabrica/result.png"
    assert request.input_payload["approved_defects"][0]["defect_type"] == "generated_artifact_size_sanity"
    assert request.input_payload["approved_defects"][0]["region"] == "generated_result"
    assert request.input_payload["immutable_regions"] == [
        "face",
        "identity",
        "body_shape",
        "pose",
        "unrelated_garment_details",
    ]
    assert request.artifact_references[0].purpose == "generated_result"
    assert request.artifact_references[0].size_bytes == 128


@pytest.mark.asyncio
async def test_repair_agent_planner_returns_unsafe_when_agent_invocation_fails() -> None:
    storage, result, report = _repair_context()
    invocation_service = _FailedInvocationServiceStub("Repair Agent invalid output.")
    planner = TryOnRepairAgentPlanner(
        object_storage=storage,
        invocation_service=invocation_service,
        timeout_seconds=90.0,
        preferred_model="repair-agent-stub",
    )

    plan = await planner.create_plan(job_id="job-1", result=result, quality_report=report)

    assert plan.repair_scope == "unsafe"
    assert plan.confidence == pytest.approx(0.0)
    assert "Repair Agent invalid output." in plan.limitations


def _repair_context() -> tuple[InMemoryObjectStorage, TryOnResult, TryOnQualityReport]:
    storage = InMemoryObjectStorage()
    object_key = "fitfabrica/result.png"
    storage.put_bytes(object_key=object_key, payload=b"x" * 128, content_type="image/png")
    image = TryOnResultImage(
        kind="generated_artifact",
        url=f"memory://{object_key}",
        alt="Generated Try-On result",
    )
    image._artifact_object_key = object_key
    report = TryOnQualityReport(
        verdict="repair_recommended",
        confidence=0.74,
        checks=[
            TryOnQualityCheck(
                name="generated_artifact_size_sanity",
                status="warning",
                confidence=0.74,
                message="Small local background artifact should be repaired.",
            )
        ],
        limitations=[],
    )
    return (
        storage,
        TryOnResult(
            job_id="job-1",
            workflow_type=TryOnWorkflowType.TRY_ON,
            result_image=image,
            quality_report=report,
            stylist_note="Original result.",
            input_metadata=[],
        ),
        report,
    )
