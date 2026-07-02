"""Repair Agent planner adapter for Try-On image-editing repair."""

from __future__ import annotations

from hashlib import sha256
import mimetypes

from src.adapters.storage.contracts import ObjectStorage
from src.adk_agents.repair_agent.contracts import (
    RepairAgentRequest,
    RepairDefectInput,
    RepairInstructionContract,
)
from src.adk_agents.repair_agent.deploy_config import RepairAgentDeployConfig
from src.adk_agents.repair_agent.prompt_config import REPAIR_AGENT_INSTRUCTION
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.domain.try_on import TryOnQualityReport, TryOnResult
from src.use_cases.agents.invocation_service import AgentInvocationService

_IMMUTABLE_REGIONS = [
    "face",
    "identity",
    "body_shape",
    "pose",
    "unrelated_garment_details",
]


class TryOnRepairAgentPlanner:
    """Create strict local repair plans through the canonical AgentInvocationService."""

    def __init__(
        self,
        *,
        object_storage: ObjectStorage,
        invocation_service: AgentInvocationService,
        timeout_seconds: float,
        preferred_model: str | None,
    ) -> None:
        """Store dependencies and versioned Repair Agent config."""

        self._object_storage = object_storage
        self._invocation_service = invocation_service
        self._timeout_seconds = timeout_seconds
        self._config = RepairAgentDeployConfig()
        self._preferred_model = preferred_model or self._config.model

    async def create_plan(
        self,
        *,
        job_id: str,
        result: TryOnResult,
        quality_report: TryOnQualityReport,
    ) -> RepairInstructionContract:
        """Return one backend-validated repair plan or an unsafe fail-closed plan."""

        generated_object_key = result.result_image._artifact_object_key
        if result.result_image.kind != "generated_artifact" or not generated_object_key:
            return _unsafe_plan("Repair Agent requires a generated artifact result image.")
        defects = _approved_defects(quality_report)
        if not defects:
            return _unsafe_plan("Repair Agent requires backend-approved failed or warning quality checks.")

        try:
            artifact_reference = _artifact_reference(
                object_storage=self._object_storage,
                object_key=generated_object_key,
            )
        except Exception as exc:  # noqa: BLE001
            return _unsafe_plan(f"Repair Agent could not read generated artifact: {exc}")

        request_payload = RepairAgentRequest(
            generated_image_object_key=generated_object_key,
            approved_defects=defects,
            immutable_regions=list(_IMMUTABLE_REGIONS),
        )
        envelope = await self._invocation_service.invoke(
            request=AgentInvocationRequest(
                agent_name=self._config.name,
                prompt_version=self._config.prompt_version,
                contract_version=self._config.contract_version,
                trace_id=job_id,
                workflow_type="try_on",
                repair_reason="quality_repair_recommended",
                prompt=REPAIR_AGENT_INSTRUCTION,
                input_payload=request_payload.model_dump(mode="json"),
                artifact_references=[artifact_reference],
                response_schema=RepairInstructionContract.model_json_schema(),
                timeout_seconds=self._timeout_seconds,
                preferred_model=self._preferred_model,
            ),
            output_contract=RepairInstructionContract,
        )
        if (
            envelope.status != AgentRuntimeStatus.SUCCEEDED
            or envelope.validation_status != AgentValidationStatus.PASSED
            or envelope.output is None
        ):
            message = envelope.error.message if envelope.error is not None else "Repair Agent did not return a plan."
            return _unsafe_plan(message)
        try:
            return RepairInstructionContract.model_validate(envelope.output)
        except ValueError as exc:
            return _unsafe_plan(f"Repair Agent returned an invalid repair plan: {exc}")


def _approved_defects(quality_report: TryOnQualityReport) -> list[RepairDefectInput]:
    """Map backend-approved failed/warning quality checks into Repair Agent defect inputs."""

    defects: list[RepairDefectInput] = []
    for check in quality_report.checks:
        if check.status not in {"failed", "warning"}:
            continue
        defects.append(
            RepairDefectInput(
                defect_type=check.name,
                region="generated_result",
                evidence=check.message,
            )
        )
    return defects


def _artifact_reference(*, object_storage: ObjectStorage, object_key: str) -> AgentArtifactReference:
    """Build an artifact reference for the generated result image."""

    payload = object_storage.get_bytes(object_key)
    return AgentArtifactReference(
        purpose="generated_result",
        object_key=object_key,
        content_type=_content_type(object_key),
        size_bytes=len(payload),
        sha256=sha256(payload).hexdigest(),
    )


def _content_type(object_key: str) -> str:
    """Infer a supported image content type from the generated artifact key."""

    guessed, _encoding = mimetypes.guess_type(object_key)
    if guessed in {"image/jpeg", "image/png", "image/webp"}:
        return guessed
    return "image/png"


def _unsafe_plan(message: str) -> RepairInstructionContract:
    """Return a typed unsafe plan that blocks image editing downstream."""

    return RepairInstructionContract(
        repair_scope="unsafe",
        target_issues=[],
        editing_instructions=[],
        confidence=0.0,
        limitations=[message],
        region_instructions=[],
    )
