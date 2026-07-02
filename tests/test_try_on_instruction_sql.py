from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.database.sql.try_on_models import TryOnInstructionRow
from src.adapters.database.sql.try_on_serialization import job_from_models, job_to_models
from src.domain.try_on import TryOnJob, TryOnJobStatus
from src.domain.try_on_instruction import TryOnGenerationInstruction


def test_instruction_is_persisted_as_separate_child_entity() -> None:
    assert TryOnInstructionRow.__tablename__ == "try_on_instructions"


def test_instruction_serialization_round_trip() -> None:
    now = datetime.now(timezone.utc)
    job = TryOnJob(
        job_id="try-on-instruction-1",
        status=TryOnJobStatus.ACCEPTED,
        created_at=now,
        updated_at=now,
        instruction=TryOnGenerationInstruction(
            invocation_id="instruction-1",
            prompt_version="try_on.v1",
            contract_version="try_on.contract.v1",
            instruction_summary="Preserve approved constraints.",
            confidence=0.92,
            uncertainty_level="low",
        ),
    )

    serialized = job_to_models(job)
    restored = job_from_models(
        job_row=serialized.job_row,
        stored_input_rows=[],
        status_event_rows=[],
        cost_event_rows=[],
        result_row=None,
        error_row=None,
        human_identity_analysis_row=None,
        instruction_row=serialized.instruction_row,
    )

    assert restored.instruction is not None
    assert restored.instruction.invocation_id == "instruction-1"
    assert restored.instruction.instruction_summary == "Preserve approved constraints."
