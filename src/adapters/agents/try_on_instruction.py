"""Provider-neutral Try-On instruction adapter."""

from __future__ import annotations

from src.adk_agents.try_on_agent.contracts import TryOnInstructionContract
from src.adk_agents.try_on_agent.deploy_config import TryOnAgentDeployConfig
from src.adk_agents.try_on_agent.prompt_config import TRY_ON_INSTRUCTION
from src.domain.agent_runtime import AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.domain.try_on import TryOnWearControlSelection
from src.domain.try_on_instruction import TryOnGenerationInstruction, TryOnInstructionVerdict, TryOnOutfitSlotInstruction
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundle
from src.use_cases.try_on.instruction_errors import TryOnInstructionFailure
from src.use_cases.try_on.instruction_policy import TryOnInstructionContinuationPolicy


class TryOnInstructionAgentAdapter:
    """Create a validated generation instruction from approved analyses only."""

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
        self._preferred_model = preferred_model
        self._config = TryOnAgentDeployConfig()
        self._policy = TryOnInstructionContinuationPolicy(minimum_confidence=minimum_confidence)

    async def create(
        self,
        *,
        job_id: str,
        analysis_bundle: TryOnAnalysisBundle,
        wear_control_selections: list[TryOnWearControlSelection] | None = None,
    ) -> TryOnGenerationInstruction:
        """Return one fail-closed instruction with no artifact access."""
        selections = wear_control_selections or []
        envelope = await self._invocation_service.invoke(
            request=AgentInvocationRequest(
                agent_name=self._config.name,
                prompt_version=self._config.prompt_version,
                contract_version=self._config.contract_version,
                trace_id=job_id,
                prompt=TRY_ON_INSTRUCTION,
                input_payload={
                    "human_analysis": analysis_bundle.human_identity.model_dump(mode="json"),
                    "garment_analysis": analysis_bundle.garment_identity.model_dump(mode="json"),
                    "garment_slot_analyses": [
                        item.model_dump(mode="json") for item in analysis_bundle.garment_slot_analyses
                    ],
                    "material_analysis": analysis_bundle.material_texture.model_dump(mode="json"),
                    "user_options": {
                        "wear_control_selections": [item.model_dump(mode="json") for item in selections],
                    },
                },
                artifact_references=[],
                response_schema=TryOnInstructionContract.model_json_schema(),
                timeout_seconds=self._timeout_seconds,
                preferred_model=self._preferred_model,
            ),
            output_contract=TryOnInstructionContract,
        )
        if (
            envelope.status != AgentRuntimeStatus.SUCCEEDED
            or envelope.validation_status != AgentValidationStatus.PASSED
            or envelope.output is None
        ):
            raise TryOnInstructionFailure(
                safe_code=envelope.error.code if envelope.error is not None else "try_on_instruction_invalid_output"
            )
        try:
            output = TryOnInstructionContract.model_validate(envelope.output)
        except ValueError as exc:
            raise TryOnInstructionFailure(safe_code="try_on_instruction_invalid_output") from exc
        decision = self._policy.evaluate(
            preserve_face=output.preserve_face,
            preserve_body_shape=output.preserve_body_shape,
            preserve_pose=output.preserve_pose,
            garment_focus_point_count=len(output.garment_focus_points),
            generation_exclusion_count=len(output.generation_exclusions),
            evidence_count=len(output.evidence),
            confidence=output.confidence,
            uncertainty_level=output.uncertainty_level.value,
        )
        if decision.verdict == TryOnInstructionVerdict.BLOCKED:
            raise TryOnInstructionFailure(safe_code=decision.rejection_reasons[0])
        instruction = TryOnGenerationInstruction(
            invocation_id=envelope.invocation_id,
            prompt_version=envelope.prompt_version,
            contract_version=envelope.contract_version,
            instruction_summary=output.instruction_summary,
            preserve_face=output.preserve_face,
            preserve_body_shape=output.preserve_body_shape,
            preserve_pose=output.preserve_pose,
            garment_focus_points=output.garment_focus_points,
            outfit_slot_focus_points=[item.model_dump(mode="json") for item in output.outfit_slot_focus_points],
            styling_focus_points=output.styling_focus_points,
            generation_exclusions=output.generation_exclusions,
            expected_framing=output.expected_framing,
            evidence=[item.model_dump(mode="json") for item in output.evidence],
            confidence=output.confidence,
            limitations=output.limitations,
            uncertainty_level=output.uncertainty_level.value,
        )
        return _apply_wear_control_selections(instruction, selections)


def _apply_wear_control_selections(
    instruction: TryOnGenerationInstruction,
    selections: list[TryOnWearControlSelection],
) -> TryOnGenerationInstruction:
    """Add backend-validated wear-control instructions to matching outfit slots."""
    if not selections:
        return instruction
    _raise_on_wear_control_conflicts(instruction, selections)
    selection_by_slot = {selection.slot_role: selection for selection in selections}
    updated_slots = []
    seen_slots: set[str] = set()
    for slot_instruction in instruction.outfit_slot_focus_points:
        selection = selection_by_slot.get(slot_instruction.slot_role)
        if selection is None:
            updated_slots.append(slot_instruction)
            continue
        seen_slots.add(selection.slot_role)
        updated_slots.append(
            slot_instruction.model_copy(
                update={
                    "focus_points": [
                        *slot_instruction.focus_points,
                        selection.instruction_template,
                    ]
                }
            )
        )
    for selection in selections:
        if selection.slot_role in seen_slots:
            continue
        updated_slots.append(
            TryOnOutfitSlotInstruction(
                slot_role=selection.slot_role,
                garment_type=selection.garment_type,
                focus_points=[selection.instruction_template],
                generation_exclusions=[],
            )
        )
    return instruction.model_copy(update={"outfit_slot_focus_points": updated_slots})


def _raise_on_wear_control_conflicts(
    instruction: TryOnGenerationInstruction,
    selections: list[TryOnWearControlSelection],
) -> None:
    """Fail closed when the agent returned an instruction that contradicts a backend-selected wear control."""
    selection_by_slot = {selection.slot_role: selection for selection in selections}
    for slot_instruction in instruction.outfit_slot_focus_points:
        selection = selection_by_slot.get(slot_instruction.slot_role)
        if selection is None:
            continue
        text = " ".join(
            [
                *slot_instruction.focus_points,
                *slot_instruction.generation_exclusions,
            ]
        ).lower()
        if _has_wear_control_conflict(selection.resolved_control_code, text):
            raise TryOnInstructionFailure(safe_code="wear_control_instruction_conflict")


def _has_wear_control_conflict(control_code: str, text: str) -> bool:
    """Return whether one instruction text contradicts a normalized wear-control code."""
    normalized = control_code.strip().lower()
    if normalized == "untucked":
        return "tuck the" in text or "tucked into" in text or "do not keep" in text and "untucked" in text
    if normalized == "tucked":
        return "untucked" in text or "do not tuck" in text
    if normalized == "open_front":
        return "buttoned closed" in text or "close the front" in text or "closed front" in text
    if normalized == "buttoned_closed":
        return "open front" in text or "keep the coat open" in text or "leave open" in text
    return False
