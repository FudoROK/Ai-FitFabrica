"""Human Identity analysis adapter for the backend-owned Try-On workflow."""

from __future__ import annotations

from src.adk_agents.human_identity_agent.contracts import HumanIdentityContract, HumanIdentityRequest
from src.adk_agents.human_identity_agent.deploy_config import HumanIdentityAgentDeployConfig
from src.adk_agents.human_identity_agent.prompt_config import HUMAN_IDENTITY_INSTRUCTION
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.domain.try_on import (
    TryOnHumanIdentityAnalysis,
    TryOnHumanIdentityEvidence,
    TryOnHumanIdentityPreservationTarget,
    TryOnStoredInput,
    TryOnUploadRole,
)
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.try_on.human_identity_errors import HumanIdentityAnalysisFailure
from src.use_cases.try_on.human_identity_policy import HumanIdentityContinuationPolicy


class HumanIdentityAnalysisAdapter:
    """Invoke and map the versioned Human Identity agent contract."""

    def __init__(
        self,
        *,
        invocation_service: AgentInvocationService,
        policy: HumanIdentityContinuationPolicy,
        timeout_seconds: float,
        preferred_model: str | None,
    ) -> None:
        """Store canonical invocation dependencies and backend policy."""

        self._invocation_service = invocation_service
        self._policy = policy
        self._timeout_seconds = timeout_seconds
        self._config = HumanIdentityAgentDeployConfig()
        self._preferred_model = preferred_model or self._config.model

    async def analyze(
        self,
        *,
        job_id: str,
        stored_inputs: list[TryOnStoredInput],
    ) -> TryOnHumanIdentityAnalysis:
        """Return one validated and policy-evaluated human analysis snapshot."""

        human_input = next((item for item in stored_inputs if item.role == TryOnUploadRole.HUMAN_PHOTO), None)
        if human_input is None or not human_input.object_key:
            raise HumanIdentityAnalysisFailure(safe_code="human_artifact_missing")
        agent_request = HumanIdentityRequest(human_photo_object_key=human_input.object_key)
        envelope = await self._invocation_service.invoke(
            request=AgentInvocationRequest(
                agent_name=self._config.name,
                prompt_version=self._config.prompt_version,
                contract_version=self._config.contract_version,
                trace_id=job_id,
                prompt=HUMAN_IDENTITY_INSTRUCTION,
                input_payload={
                    "human_photo_object_key": agent_request.human_photo_object_key,
                    "requested_checks": list(agent_request.requested_checks),
                },
                artifact_references=[
                    AgentArtifactReference(
                        purpose="human_photo",
                        object_key=human_input.object_key,
                        content_type=human_input.content_type,
                        size_bytes=human_input.size_bytes,
                        sha256=human_input.sha256,
                    )
                ],
                response_schema=HumanIdentityContract.model_json_schema(),
                timeout_seconds=self._timeout_seconds,
                preferred_model=self._preferred_model,
            ),
            output_contract=HumanIdentityContract,
        )
        if (
            envelope.status != AgentRuntimeStatus.SUCCEEDED
            or envelope.validation_status != AgentValidationStatus.PASSED
            or envelope.output is None
        ):
            raise HumanIdentityAnalysisFailure(
                safe_code=envelope.error.code if envelope.error is not None else "human_identity_invalid_output"
            )
        output = HumanIdentityContract.model_validate(envelope.output)
        decision = self._policy.evaluate(
            face_visibility=output.face_visibility,
            body_region_visibility=output.body_region_visibility,
            preservation_target_count=len(output.preservation_targets),
            confidence=output.confidence,
            uncertainty_level=output.uncertainty_level.value,
            subject_count=output.subject_count,
            crop_quality=output.crop_quality,
            try_on_body_coverage=output.try_on_body_coverage,
            occlusion_risk=output.occlusion_risk,
            required_regions_missing=output.required_regions_missing,
        )
        return TryOnHumanIdentityAnalysis(
            invocation_id=envelope.invocation_id,
            prompt_version=envelope.prompt_version,
            contract_version=envelope.contract_version,
            face_visibility=output.face_visibility,
            pose_summary=output.pose_summary,
            body_region_visibility=output.body_region_visibility,
            subject_count=output.subject_count,
            crop_quality=output.crop_quality,
            try_on_body_coverage=output.try_on_body_coverage,
            occlusion_risk=output.occlusion_risk,
            required_regions_missing=output.required_regions_missing,
            preservation_targets=[
                TryOnHumanIdentityPreservationTarget(
                    attribute_name=item.attribute_name,
                    preservation_reason=item.preservation_reason,
                )
                for item in output.preservation_targets
            ],
            confidence=output.confidence,
            limitations=output.limitations,
            evidence=[
                TryOnHumanIdentityEvidence(
                    source_type=item.source_type,
                    source_ref=item.source_ref,
                    observation=item.observation,
                    confidence=item.confidence,
                )
                for item in output.evidence
            ],
            uncertainty_level=output.uncertainty_level.value,
            unknowns=output.unknowns,
            verdict=decision.verdict,
            rejection_reasons=decision.rejection_reasons,
        )
