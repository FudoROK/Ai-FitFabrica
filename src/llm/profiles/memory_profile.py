from __future__ import annotations

from dataclasses import dataclass

from ...runtime_agents.memory_agent.contracts.daily import DailyMemoryContract

from .contracts import FinalProfileInterface, SemanticValidationContext, ValidationResult


@dataclass(frozen=True)
class MemoryProfileOutput:
    memory_payload: DailyMemoryContract


class MemoryProfile(FinalProfileInterface[MemoryProfileOutput]):
    """Memory profile compute-only parser/validator without side effects."""

    def parse(self, raw_payload: DailyMemoryContract) -> MemoryProfileOutput:
        if not isinstance(raw_payload, DailyMemoryContract):
            raise TypeError("MemoryProfile.parse expects DailyMemoryContract")
        return MemoryProfileOutput(memory_payload=raw_payload)

    def validate(self, typed_output: MemoryProfileOutput) -> ValidationResult:
        if not isinstance(typed_output.memory_payload, DailyMemoryContract):
            return ValidationResult.failure()
        return ValidationResult.success()

    def semantic_validate(
        self,
        typed_output: MemoryProfileOutput,
        context: SemanticValidationContext,
    ) -> ValidationResult:
        _ = (typed_output, context)
        return ValidationResult.success()
