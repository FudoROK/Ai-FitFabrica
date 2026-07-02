"""Material / Texture analysis adapter for backend-owned Try-On workflows."""

from __future__ import annotations

from src.adk_agents.material_texture_agent.contracts import MaterialTextureContract, MaterialTextureRequest
from src.adk_agents.material_texture_agent.deploy_config import MaterialTextureAgentDeployConfig
from src.adk_agents.material_texture_agent.prompt_config import MATERIAL_TEXTURE_INSTRUCTION
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.domain.material_texture import MaterialTextureVerdict
from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.domain.try_on_analysis import TryOnMaterialTextureAnalysis
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.material_texture_policy import MaterialTextureContinuationPolicy
from src.use_cases.try_on.analysis_errors import MaterialTextureAnalysisFailure


class TryOnMaterialTextureAnalysisAdapter:
    """Invoke and map the versioned Material / Texture contract for Try-On."""

    def __init__(
        self,
        *,
        invocation_service: AgentInvocationService,
        minimum_confidence: float,
        timeout_seconds: float,
        preferred_model: str | None,
    ) -> None:
        self._invocation_service = invocation_service
        self._minimum_confidence = minimum_confidence
        self._timeout_seconds = timeout_seconds
        self._config = MaterialTextureAgentDeployConfig()
        self._preferred_model = preferred_model or self._config.model
        self._policy = MaterialTextureContinuationPolicy(minimum_confidence=minimum_confidence)

    async def analyze(self, *, job_id: str, stored_inputs: list[TryOnStoredInput]) -> TryOnMaterialTextureAnalysis:
        """Return one validated fail-closed material snapshot."""
        garment_input = next((item for item in stored_inputs if item.role == TryOnUploadRole.GARMENT_PHOTO), None)
        if garment_input is None or not garment_input.object_key:
            raise MaterialTextureAnalysisFailure(safe_code="material_artifact_missing")
        agent_request = MaterialTextureRequest(garment_photo_object_key=garment_input.object_key)
        envelope = await self._invocation_service.invoke(
            request=AgentInvocationRequest(
                agent_name=self._config.name,
                prompt_version=self._config.prompt_version,
                contract_version=self._config.contract_version,
                trace_id=job_id,
                prompt=MATERIAL_TEXTURE_INSTRUCTION,
                input_payload={
                    "garment_photo_object_key": agent_request.garment_photo_object_key,
                    "trusted_material_facts": list(agent_request.trusted_material_facts),
                },
                artifact_references=[
                    AgentArtifactReference(
                        purpose="garment_photo",
                        object_key=garment_input.object_key,
                        content_type=garment_input.content_type,
                        size_bytes=garment_input.size_bytes,
                        sha256=garment_input.sha256,
                    )
                ],
                response_schema=MaterialTextureContract.model_json_schema(),
                timeout_seconds=self._timeout_seconds,
                preferred_model=self._preferred_model,
            ),
            output_contract=MaterialTextureContract,
        )
        if envelope.status != AgentRuntimeStatus.SUCCEEDED or envelope.validation_status != AgentValidationStatus.PASSED or envelope.output is None:
            raise MaterialTextureAnalysisFailure(
                safe_code=envelope.error.code if envelope.error is not None else "material_texture_invalid_output"
            )
        try:
            output = MaterialTextureContract.model_validate(envelope.output)
        except ValueError as exc:
            raise MaterialTextureAnalysisFailure(safe_code="material_texture_invalid_output") from exc
        decision = self._policy.evaluate(
            visible_material_signal_count=len(output.visible_material_signals),
            texture_signal_count=len(output.texture_signals),
            observation_count=len(output.observations),
            evidence_count=len(output.evidence),
            confidence=output.confidence,
            uncertainty_level=output.uncertainty_level.value,
        )
        if decision.verdict == MaterialTextureVerdict.BLOCKED:
            raise MaterialTextureAnalysisFailure(safe_code=decision.rejection_reasons[0])
        return TryOnMaterialTextureAnalysis(
            invocation_id=envelope.invocation_id,
            prompt_version=envelope.prompt_version,
            contract_version=envelope.contract_version,
            visible_material_signals=output.visible_material_signals,
            texture_signals=output.texture_signals,
            evidence_note=output.evidence_note,
            observations=[item.model_dump() for item in output.observations],
            evidence=[item.model_dump() for item in output.evidence],
            confidence=output.confidence,
            limitations=output.limitations,
            composition_status=output.composition_status,
            uncertainty_level=output.uncertainty_level.value,
            alternative_interpretations=output.alternative_interpretations,
        )
