from __future__ import annotations

import logging

from src.domain.context_validation import (
    ContextStateQuery,
    ContextStateQueryResult,
    ContextValidationError,
    ContextValidationErrorCode,
)
from src.domain.contracts.context_validation import SourceContextStateRepository

logger = logging.getLogger(__name__)


class QueryContextStateUseCase:
    """Read confirmed facts and candidate states without semantic collapse."""

    def __init__(self, *, repository: SourceContextStateRepository) -> None:
        """Initialize the query use case with backend-owned persistence."""
        self.repository = repository

    async def execute(self, *, query: ContextStateQuery) -> ContextStateQueryResult:
        """Return separated read-model collections for the requested tenant."""
        try:
            candidate_records = (
                await self.repository.list_candidates(tenant_id=query.actor_context.tenant_id)
                if query.include_candidates or query.include_confirmed_facts
                else []
            )
            visible_candidates = [
                candidate for candidate in candidate_records if candidate.actor_context == query.actor_context
            ]
            visible_candidate_ids = {candidate.candidate_id for candidate in visible_candidates}
            confirmed_facts = (
                [
                    fact
                    for fact in await self.repository.list_confirmed_facts(tenant_id=query.actor_context.tenant_id)
                    if fact.candidate_id in visible_candidate_ids
                ]
                if query.include_confirmed_facts
                else []
            )
            candidates = visible_candidates if query.include_candidates else []
        except Exception:
            logger.exception(
                "source_context_state_query_failed",
                extra={"tenant_id": query.actor_context.tenant_id, "actor_id": query.actor_context.actor_id},
            )
            return ContextStateQueryResult(
                ok=False,
                error=ContextValidationError(
                    code=ContextValidationErrorCode.PERSISTENCE_FAILURE,
                    message="Source-context persistence operation failed.",
                ),
            )
        return ContextStateQueryResult(confirmed_facts=confirmed_facts, candidates=candidates)
