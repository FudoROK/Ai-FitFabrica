"""Garment Identity analysis adapter for backend-owned Try-On workflows."""

from __future__ import annotations

from src.adk_agents.garment_identity_agent.contracts import GarmentIdentityContract, GarmentIdentityRequest
from src.adk_agents.garment_identity_agent.deploy_config import GarmentIdentityAgentDeployConfig
from src.adk_agents.garment_identity_agent.prompt_config import GARMENT_IDENTITY_INSTRUCTION
from src.adapters.agents.garment_taxonomy_mapping import map_garment_taxonomy_outputs
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.domain.garment_identity import GarmentIdentityVerdict, GarmentIdentityWorkflowMode
from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.domain.try_on_analysis import TryOnGarmentIdentityAnalysis
from src.use_cases.garment_identity_policy import GarmentIdentityContinuationPolicy
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.garment_taxonomy.service import GarmentTaxonomyService
from src.use_cases.try_on.analysis_errors import GarmentIdentityAnalysisFailure


class TryOnGarmentIdentityAnalysisAdapter:
    """Invoke and map the versioned Garment Identity contract for Try-On."""

    def __init__(
        self,
        *,
        invocation_service: AgentInvocationService,
        minimum_confidence: float,
        timeout_seconds: float,
        preferred_model: str | None,
        taxonomy_service: GarmentTaxonomyService | None = None,
    ) -> None:
        self._invocation_service = invocation_service
        self._minimum_confidence = minimum_confidence
        self._timeout_seconds = timeout_seconds
        self._config = GarmentIdentityAgentDeployConfig()
        self._preferred_model = preferred_model or self._config.model
        self._policy = GarmentIdentityContinuationPolicy(minimum_confidence=minimum_confidence)
        self._taxonomy_service = taxonomy_service

    async def analyze(self, *, job_id: str, stored_inputs: list[TryOnStoredInput]) -> TryOnGarmentIdentityAnalysis:
        """Return one validated fail-closed garment snapshot."""
        garment_input = select_primary_garment_input(stored_inputs)
        if garment_input is None or not garment_input.object_key:
            raise GarmentIdentityAnalysisFailure(safe_code="garment_artifact_missing")
        agent_request = GarmentIdentityRequest(garment_photo_object_key=garment_input.object_key)
        envelope = await self._invocation_service.invoke(
            request=AgentInvocationRequest(
                agent_name=self._config.name,
                prompt_version=self._config.prompt_version,
                contract_version=self._config.contract_version,
                trace_id=job_id,
                prompt=GARMENT_IDENTITY_INSTRUCTION,
                input_payload={
                    "garment_photo_object_key": agent_request.garment_photo_object_key,
                    "trusted_product_facts": list(agent_request.trusted_product_facts),
                },
                artifact_references=[_artifact_reference(garment_input, purpose="garment_photo")],
                response_schema=GarmentIdentityContract.model_json_schema(),
                timeout_seconds=self._timeout_seconds,
                preferred_model=self._preferred_model,
            ),
            output_contract=GarmentIdentityContract,
        )
        if envelope.status != AgentRuntimeStatus.SUCCEEDED or envelope.validation_status != AgentValidationStatus.PASSED or envelope.output is None:
            raise GarmentIdentityAnalysisFailure(
                safe_code=envelope.error.code if envelope.error is not None else "garment_identity_invalid_output"
            )
        output = GarmentIdentityContract.model_validate(envelope.output)
        decision = self._policy.evaluate(
            workflow_mode=GarmentIdentityWorkflowMode.TRY_ON,
            garment_count=output.garment_count,
            garment_visibility=output.garment_visibility,
            crop_quality=output.crop_quality,
            try_on_garment_coverage=output.try_on_garment_coverage,
            product_card_coverage=output.product_card_coverage,
            occlusion_risk=output.occlusion_risk,
            required_regions_missing=output.required_regions_missing,
            ambiguous_target=output.ambiguous_target,
            confidence=output.confidence,
            uncertainty_level=output.uncertainty_level.value,
        )
        if decision.verdict == GarmentIdentityVerdict.BLOCKED:
            raise GarmentIdentityAnalysisFailure(safe_code=decision.rejection_reasons[0])
        taxonomy_mapping = await map_garment_taxonomy_outputs(
            job_id=job_id,
            output=output,
            taxonomy_service=self._taxonomy_service,
        )
        return TryOnGarmentIdentityAnalysis(
            invocation_id=envelope.invocation_id,
            prompt_version=envelope.prompt_version,
            contract_version=envelope.contract_version,
            garment_type=output.garment_type,
            taxonomy_parent=output.taxonomy_parent,
            taxonomy_confidence=output.taxonomy_confidence,
            wear_control_candidates=taxonomy_mapping.wear_control_candidates,
            unknown_taxonomy_candidate=taxonomy_mapping.unknown_taxonomy_candidate,
            garment_count=output.garment_count,
            target_garment_index=output.target_garment_index,
            target_garment_description=output.target_garment_description,
            garment_visibility=output.garment_visibility,
            crop_quality=output.crop_quality,
            try_on_garment_coverage=output.try_on_garment_coverage,
            product_card_coverage=output.product_card_coverage,
            occlusion_risk=output.occlusion_risk,
            required_regions_missing=output.required_regions_missing,
            ambiguous_target=output.ambiguous_target,
            dominant_color=output.dominant_color,
            secondary_colors=output.secondary_colors,
            silhouette_summary=output.silhouette_summary,
            preserved_details=output.preserved_details,
            visual_details=[item.model_dump() for item in output.visual_details],
            evidence=[item.model_dump() for item in output.evidence],
            confidence=output.confidence,
            limitations=output.limitations,
            uncertainty_level=output.uncertainty_level.value,
            unknowns=output.unknowns,
        )


def _artifact_reference(stored_input: TryOnStoredInput, *, purpose: str) -> AgentArtifactReference:
    """Map a verified stored input into the canonical agent artifact contract."""
    return AgentArtifactReference(
        purpose=purpose,
        object_key=stored_input.object_key or "",
        content_type=stored_input.content_type,
        size_bytes=stored_input.size_bytes,
        sha256=stored_input.sha256,
    )


def select_primary_garment_input(stored_inputs: list[TryOnStoredInput]) -> TryOnStoredInput | None:
    """Return the single primary garment used by the current v1 analysis adapter."""
    role_priority = [
        TryOnUploadRole.GARMENT_PHOTO,
        TryOnUploadRole.FULL_BODY_GARMENT_PHOTO,
        TryOnUploadRole.UPPER_GARMENT_PHOTO,
        TryOnUploadRole.LOWER_GARMENT_PHOTO,
        TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO,
    ]
    for role in role_priority:
        match = next((item for item in stored_inputs if item.role == role), None)
        if match is not None:
            return match
    return None
