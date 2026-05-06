from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from src.domain.context_validation import (
    ConfirmedFact,
    ContextValidationError,
    ContextValidationErrorCode,
    SourceContextCandidate,
    SourceContextCandidateStatus,
    SourceContextValidationCommand,
    SourceContextValidationResult,
    ValidationDecision,
)
from src.domain.contracts.context_validation import SourceContextStateRepository

logger = logging.getLogger(__name__)


class ValidateSourceContextCandidateUseCase:
    """Apply explicit validation decisions to pending source-context candidates."""

    def __init__(self, *, repository: SourceContextStateRepository) -> None:
        """Initialize the use case with backend-owned persistence."""
        self.repository = repository

    async def execute(self, *, command: SourceContextValidationCommand) -> SourceContextValidationResult:
        """Confirm, refine, reject, or keep open a candidate with structured outcomes."""
        try:
            candidate = await self.repository.get_candidate(candidate_id=command.candidate_id)
        except Exception:
            logger.exception(
                "source_context_candidate_load_failed",
                extra={"candidate_id": command.candidate_id, "tenant_id": command.actor_context.tenant_id},
            )
            return self._persistence_error(audit_summary="candidate_validation_load_failed")
        if candidate is None:
            return self._error(
                code=ContextValidationErrorCode.UNKNOWN_CANDIDATE,
                message="Candidate was not found.",
                audit_summary="candidate_validation_unknown_candidate",
            )
        if not self._actor_can_validate(candidate=candidate, command=command):
            logger.warning(
                "source_context_candidate_authority_rejected",
                extra={
                    "candidate_id": candidate.candidate_id,
                    "candidate_tenant_id": candidate.actor_context.tenant_id,
                    "command_tenant_id": command.actor_context.tenant_id,
                },
            )
            return self._error(
                code=ContextValidationErrorCode.MISSING_AUTHORITY,
                message="Actor context is not authorized to validate this candidate.",
                audit_summary="candidate_validation_missing_authority",
            )

        resolvable_statuses = {SourceContextCandidateStatus.PENDING_CONFIRMATION, SourceContextCandidateStatus.OPEN}
        if candidate.status not in resolvable_statuses:
            return await self._handle_repeated_or_invalid_decision(candidate=candidate, command=command)

        if command.decision in {ValidationDecision.CONFIRM, ValidationDecision.REFINE}:
            return await self._promote_candidate(candidate=candidate, command=command)
        if command.decision == ValidationDecision.REJECT:
            return await self._update_candidate_status(
                candidate=candidate,
                status=SourceContextCandidateStatus.REJECTED,
                command=command,
                audit_summary="candidate_rejected",
            )
        return await self._update_candidate_status(
            candidate=candidate,
            status=SourceContextCandidateStatus.OPEN,
            command=command,
            audit_summary="candidate_kept_open",
        )

    async def _handle_repeated_or_invalid_decision(
        self,
        *,
        candidate: SourceContextCandidate,
        command: SourceContextValidationCommand,
    ) -> SourceContextValidationResult:
        """Return idempotent success for repeated accepted decisions and errors otherwise."""
        if candidate.status == SourceContextCandidateStatus.REJECTED and command.decision == ValidationDecision.REJECT:
            return SourceContextValidationResult(
                ok=True,
                candidate=candidate,
                audit_summary="candidate_validation_idempotent",
            )
        try:
            fact = await self.repository.get_confirmed_fact_by_candidate_id(candidate_id=candidate.candidate_id)
        except Exception:
            logger.exception(
                "source_context_confirmed_fact_lookup_failed",
                extra={"candidate_id": candidate.candidate_id, "tenant_id": candidate.actor_context.tenant_id},
            )
            return self._persistence_error(audit_summary="candidate_validation_fact_lookup_failed")
        if fact is not None and self._is_same_promoting_decision(candidate=candidate, command=command, fact=fact):
            return SourceContextValidationResult(
                ok=True,
                candidate=candidate,
                confirmed_fact=fact,
                audit_summary="candidate_validation_idempotent",
            )
        return self._error(
            code=ContextValidationErrorCode.INVALID_TRANSITION,
            message=f"Candidate cannot transition from {candidate.status.value}.",
            audit_summary="candidate_validation_invalid_transition",
        )

    async def _promote_candidate(
        self,
        *,
        candidate: SourceContextCandidate,
        command: SourceContextValidationCommand,
    ) -> SourceContextValidationResult:
        """Promote a candidate to confirmed fact after confirm or refine."""
        value = command.refined_value.strip() if command.decision == ValidationDecision.REFINE and command.refined_value else candidate.payload.value
        status = (
            SourceContextCandidateStatus.REFINED
            if command.decision == ValidationDecision.REFINE
            else SourceContextCandidateStatus.CONFIRMED
        )
        fact = ConfirmedFact(
            fact_id=self._fact_id(candidate=candidate, value=value),
            candidate_id=candidate.candidate_id,
            tenant_id=candidate.actor_context.tenant_id,
            fact_key=candidate.payload.fact_key,
            value=value,
            source_reference=candidate.source_reference,
            created_at=datetime.now(timezone.utc),
        )
        updated_candidate = candidate.model_copy(
            update={
                "status": status,
                "updated_at": datetime.now(timezone.utc),
                "confirmed_fact_id": fact.fact_id,
                "validation_reason": command.reason,
            }
        )
        try:
            await self.repository.save_candidate_with_confirmed_fact(candidate=updated_candidate, confirmed_fact=fact)
        except Exception:
            logger.exception(
                "source_context_candidate_promotion_failed",
                extra={"candidate_id": candidate.candidate_id, "tenant_id": candidate.actor_context.tenant_id},
            )
            return self._persistence_error(audit_summary="candidate_validation_promotion_failed")
        logger.info(
            "source_context_candidate_promoted",
            extra={
                "candidate_id": candidate.candidate_id,
                "fact_id": fact.fact_id,
                "decision": command.decision.value,
            },
        )
        return SourceContextValidationResult(
            ok=True,
            candidate=updated_candidate,
            confirmed_fact=fact,
            audit_summary="candidate_promoted_to_confirmed_fact",
        )

    async def _update_candidate_status(
        self,
        *,
        candidate: SourceContextCandidate,
        status: SourceContextCandidateStatus,
        command: SourceContextValidationCommand,
        audit_summary: str,
    ) -> SourceContextValidationResult:
        """Persist a non-promoting candidate status transition."""
        updated_candidate = candidate.model_copy(
            update={"status": status, "updated_at": datetime.now(timezone.utc), "validation_reason": command.reason}
        )
        try:
            await self.repository.save_candidate(candidate=updated_candidate)
        except Exception:
            logger.exception(
                "source_context_candidate_status_save_failed",
                extra={"candidate_id": candidate.candidate_id, "tenant_id": candidate.actor_context.tenant_id},
            )
            return self._persistence_error(audit_summary="candidate_validation_status_save_failed")
        return SourceContextValidationResult(ok=True, candidate=updated_candidate, audit_summary=audit_summary)

    @staticmethod
    def _actor_can_validate(
        *,
        candidate: SourceContextCandidate,
        command: SourceContextValidationCommand,
    ) -> bool:
        """Return whether command identity matches the candidate ownership context."""
        candidate_actor = candidate.actor_context
        command_actor = command.actor_context
        return (
            candidate_actor.tenant_id == command_actor.tenant_id
            and candidate_actor.actor_id == command_actor.actor_id
            and candidate_actor.session_id == command_actor.session_id
        )

    @staticmethod
    def _is_same_promoting_decision(
        *,
        candidate: SourceContextCandidate,
        command: SourceContextValidationCommand,
        fact: ConfirmedFact,
    ) -> bool:
        """Return whether a repeated command matches the already-applied promotion."""
        if candidate.status == SourceContextCandidateStatus.CONFIRMED and command.decision == ValidationDecision.CONFIRM:
            return fact.value == candidate.payload.value
        if candidate.status == SourceContextCandidateStatus.REFINED and command.decision == ValidationDecision.REFINE:
            return fact.value == (command.refined_value or "").strip()
        return False

    @staticmethod
    def _fact_id(*, candidate: SourceContextCandidate, value: str) -> str:
        """Build a deterministic confirmed fact id from candidate and value."""
        raw = "|".join([candidate.actor_context.tenant_id, candidate.candidate_id, candidate.payload.fact_key, value])
        return f"fact_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"

    @staticmethod
    def _error(
        *,
        code: ContextValidationErrorCode,
        message: str,
        audit_summary: str,
    ) -> SourceContextValidationResult:
        """Build a structured validation failure result."""
        return SourceContextValidationResult(
            ok=False,
            error=ContextValidationError(code=code, message=message),
            audit_summary=audit_summary,
        )

    @staticmethod
    def _persistence_error(*, audit_summary: str) -> SourceContextValidationResult:
        """Build a structured persistence failure result."""
        return SourceContextValidationResult(
            ok=False,
            error=ContextValidationError(
                code=ContextValidationErrorCode.PERSISTENCE_FAILURE,
                message="Source-context persistence operation failed.",
            ),
            audit_summary=audit_summary,
        )
