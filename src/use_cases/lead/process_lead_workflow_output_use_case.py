from __future__ import annotations

import logging
from dataclasses import dataclass

from src.domain.models import Lead
from src.domain.agent_output.agent_semantic_payload_validator import (
    SemanticValidationOutcome,
    SemanticValidationResult,
    SystemPayloadSemanticValidator,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowProcessingResult:
    semantic_result: SemanticValidationResult
    side_effects_applied: bool


class ProcessWorkflowOutputUseCase:
    def __init__(
        self,
        *,
        ingest_lead_patch_use_case,
        semantic_validator: SystemPayloadSemanticValidator | None = None,
    ) -> None:
        self.ingest_lead_patch_use_case = ingest_lead_patch_use_case
        self.semantic_validator = semantic_validator or SystemPayloadSemanticValidator()

    def evaluate_semantics(self, *, system_payload) -> SemanticValidationResult:
        if not system_payload:
            return SemanticValidationResult(outcome=SemanticValidationOutcome.SEMANTIC_OK)
        return self.semantic_validator.validate(system_payload=system_payload)

    async def execute(
        self,
        *,
        system_payload,
        lead: Lead,
        external_user_id,
        event_key: str | None = None,
        semantic_result: SemanticValidationResult | None = None,
    ) -> WorkflowProcessingResult:
        if not system_payload:
            return WorkflowProcessingResult(
                semantic_result=SemanticValidationResult(outcome=SemanticValidationOutcome.SEMANTIC_OK),
                side_effects_applied=False,
            )

        semantic_result = semantic_result or self.evaluate_semantics(system_payload=system_payload)
        if semantic_result.outcome != SemanticValidationOutcome.SEMANTIC_OK:
            logger.warning(
                "side_effects_blocked_by_semantic_gate",
                extra={
                    "semantic_outcome": semantic_result.outcome,
                    "violation_codes": list(semantic_result.violation_codes),
                },
            )
            return WorkflowProcessingResult(semantic_result=semantic_result, side_effects_applied=False)

        ingested = await self.ingest_lead_patch_use_case.execute(
            lead_id=lead.lead_id,
            payload=system_payload,
            external_user_id=external_user_id,
        )
        return WorkflowProcessingResult(semantic_result=semantic_result, side_effects_applied=bool(ingested))
