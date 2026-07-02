"""Deterministic Try-On instruction creator for isolated tests."""

from src.domain.try_on_instruction import TryOnGenerationInstruction


class DeterministicTryOnInstructionAdapter:
    """Return one stable instruction derived from test-approved analyses."""

    async def create(
        self,
        *,
        job_id: str,
        analysis_bundle,
        wear_control_selections=None,
    ) -> TryOnGenerationInstruction:
        selections_by_slot = {
            selection.slot_role: selection
            for selection in (wear_control_selections or [])
        }
        return TryOnGenerationInstruction(
            invocation_id=f"test-try-on-instruction-{job_id}",
            prompt_version="try_on.test",
            contract_version="try_on.contract.test",
            instruction_summary="Preserve the approved person, garment, and visible material constraints.",
            garment_focus_points=list(analysis_bundle.garment_identity.preserved_details),
            outfit_slot_focus_points=[
                {
                    "slot_role": item.slot_role,
                    "garment_type": item.analysis.garment_type,
                    "focus_points": [
                        *list(item.analysis.preserved_details),
                        *(
                            [selections_by_slot[item.slot_role].instruction_template]
                            if item.slot_role in selections_by_slot
                            else []
                        ),
                    ],
                    "generation_exclusions": list(item.analysis.limitations),
                }
                for item in analysis_bundle.garment_slot_analyses
            ],
            confidence=1.0,
            uncertainty_level="low",
        )
