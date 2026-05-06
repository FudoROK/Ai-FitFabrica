from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.domain.context_validation import (
    ActorContext,
    ContextValidationError,
    ContextValidationErrorCode,
    SourceContextCandidateCommand,
    SourceContextValidationCommand,
    SourceContextValidationResult,
)
from src.domain.contracts.context_validation import SourceContextStateRepository
from src.use_cases.context_validation.agent_intent import SourceContextValidationIntent
from src.use_cases.context_validation.register_source_context_candidate_use_case import (
    RegisterSourceContextCandidateUseCase,
)
from src.use_cases.context_validation.validate_source_context_candidate_use_case import (
    ValidateSourceContextCandidateUseCase,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AgentIntentApplicationResult:
    """Backend-owned result for applying a parsed source-context agent intent."""

    ok: bool
    candidate_results: list[SourceContextValidationResult] = field(default_factory=list)
    validation_results: list[SourceContextValidationResult] = field(default_factory=list)
    error: ContextValidationError | None = None
    audit_summary: str = "agent_intent_not_applied"


class ApplySourceContextAgentIntentUseCase:
    """Map structured agent intent into backend candidate and validation commands."""

    def __init__(self, *, repository: SourceContextStateRepository) -> None:
        """Initialize orchestration with backend-owned persistence."""
        self.register_candidate = RegisterSourceContextCandidateUseCase(repository=repository)
        self.validate_candidate = ValidateSourceContextCandidateUseCase(repository=repository)

    async def execute(
        self,
        *,
        agent_payload: object,
        actor_context: ActorContext,
        correlation_id: str,
    ) -> AgentIntentApplicationResult:
        """Parse agent output and apply only backend-supported commands."""
        try:
            intent = SourceContextValidationIntent.parse_agent_payload(agent_payload)
        except ValueError as exc:
            logger.warning(
                "source_context_agent_intent_rejected",
                extra={"tenant_id": actor_context.tenant_id, "actor_id": actor_context.actor_id},
            )
            return AgentIntentApplicationResult(
                ok=False,
                error=ContextValidationError(
                    code=ContextValidationErrorCode.INVALID_INPUT,
                    message=str(exc),
                ),
                audit_summary="agent_intent_invalid",
            )

        candidate_results: list[SourceContextValidationResult] = []
        for index, proposal in enumerate(intent.candidate_proposals):
            result = await self.register_candidate.execute(
                command=SourceContextCandidateCommand(
                    payload=proposal.payload,
                    source_reference=proposal.source_reference,
                    actor_context=actor_context,
                    correlation_id=f"{correlation_id}:candidate:{index}",
                )
            )
            candidate_results.append(result)
            if not result.ok:
                return AgentIntentApplicationResult(
                    ok=False,
                    candidate_results=candidate_results,
                    audit_summary="agent_intent_candidate_application_failed",
                    error=result.error,
                )

        validation_results: list[SourceContextValidationResult] = []
        for index, recommendation in enumerate(intent.validation_recommendations):
            result = await self.validate_candidate.execute(
                command=SourceContextValidationCommand(
                    candidate_id=recommendation.candidate_id,
                    decision=recommendation.decision,
                    actor_context=actor_context,
                    correlation_id=f"{correlation_id}:validation:{index}",
                    refined_value=recommendation.refined_value,
                    reason=recommendation.reason,
                )
            )
            validation_results.append(result)
            if not result.ok:
                return AgentIntentApplicationResult(
                    ok=False,
                    candidate_results=candidate_results,
                    validation_results=validation_results,
                    audit_summary="agent_intent_validation_application_failed",
                    error=result.error,
                )

        return AgentIntentApplicationResult(
            ok=True,
            candidate_results=candidate_results,
            validation_results=validation_results,
            audit_summary="agent_intent_applied",
        )
