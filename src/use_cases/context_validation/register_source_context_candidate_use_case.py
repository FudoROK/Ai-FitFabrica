from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from src.domain.context_validation import (
    ContextValidationError,
    ContextValidationErrorCode,
    SourceContextCandidate,
    SourceContextCandidateCommand,
    SourceContextCandidateStatus,
    SourceContextValidationResult,
)
from src.domain.contracts.context_validation import SourceContextStateRepository

logger = logging.getLogger(__name__)


class RegisterSourceContextCandidateUseCase:
    """Create non-authoritative candidate state for source-derived context."""

    def __init__(self, *, repository: SourceContextStateRepository) -> None:
        """Initialize the use case with a backend-owned persistence port."""
        self.repository = repository

    async def execute(self, *, command: SourceContextCandidateCommand) -> SourceContextValidationResult:
        """Persist a pending candidate without promoting confirmed facts."""
        try:
            existing = await self.repository.get_candidate_by_correlation_id(correlation_id=command.correlation_id)
        except Exception:
            logger.exception(
                "source_context_candidate_lookup_failed",
                extra={"correlation_id": command.correlation_id, "tenant_id": command.actor_context.tenant_id},
            )
            return self._persistence_error(audit_summary="candidate_creation_lookup_failed")
        if existing is not None:
            if existing.actor_context != command.actor_context:
                logger.warning(
                    "source_context_candidate_idempotency_scope_rejected",
                    extra={
                        "correlation_id": command.correlation_id,
                        "existing_tenant_id": existing.actor_context.tenant_id,
                        "command_tenant_id": command.actor_context.tenant_id,
                    },
                )
                return SourceContextValidationResult(
                    ok=False,
                    error=ContextValidationError(
                        code=ContextValidationErrorCode.MISSING_AUTHORITY,
                        message="Correlation id belongs to a different actor context.",
                    ),
                    audit_summary="candidate_creation_idempotency_scope_rejected",
                )
            return SourceContextValidationResult(
                ok=True,
                candidate=existing,
                audit_summary="candidate_creation_idempotent",
            )

        candidate = SourceContextCandidate(
            candidate_id=self._candidate_id(command=command),
            payload=command.payload,
            source_reference=command.source_reference,
            actor_context=command.actor_context,
            status=SourceContextCandidateStatus.PENDING_CONFIRMATION,
            correlation_id=command.correlation_id,
            warnings=self._warnings(command=command),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        try:
            await self.repository.save_candidate(candidate=candidate)
        except Exception:
            logger.exception(
                "source_context_candidate_save_failed",
                extra={"candidate_id": candidate.candidate_id, "tenant_id": candidate.actor_context.tenant_id},
            )
            return self._persistence_error(audit_summary="candidate_creation_save_failed")
        logger.info(
            "source_context_candidate_created",
            extra={
                "candidate_id": candidate.candidate_id,
                "tenant_id": candidate.actor_context.tenant_id,
                "status": candidate.status.value,
            },
        )
        return SourceContextValidationResult(
            ok=True,
            candidate=candidate,
            audit_summary="candidate_created_pending_confirmation",
        )

    @staticmethod
    def _candidate_id(*, command: SourceContextCandidateCommand) -> str:
        """Build a deterministic candidate id from tenant, source, and correlation id."""
        raw = "|".join(
            [
                command.actor_context.tenant_id,
                command.source_reference.source_type,
                command.source_reference.source_id,
                command.correlation_id,
            ]
        )
        return f"ctx_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"

    @staticmethod
    def _warnings(*, command: SourceContextCandidateCommand) -> list[str]:
        """Return structured warnings for incomplete but acceptable candidate content."""
        warnings: list[str] = []
        if command.source_reference.source_excerpt is None:
            warnings.append("source_excerpt_missing")
        return warnings

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


def invalid_candidate_input_result(*, message: str) -> SourceContextValidationResult:
    """Build a structured invalid-input result for callers that catch DTO validation errors."""
    return SourceContextValidationResult(
        ok=False,
        error=ContextValidationError(code=ContextValidationErrorCode.INVALID_INPUT, message=message),
        audit_summary="candidate_creation_invalid_input",
    )
