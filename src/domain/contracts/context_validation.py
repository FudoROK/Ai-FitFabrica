from __future__ import annotations

from typing import Protocol

from src.domain.context_validation import ConfirmedFact, SourceContextCandidate


class SourceContextStateRepository(Protocol):
    """Persistence port for source-context candidates and confirmed facts."""

    async def get_candidate_by_correlation_id(self, *, correlation_id: str) -> SourceContextCandidate | None:
        """Return an existing candidate for idempotent candidate creation."""
        ...

    async def get_candidate(self, *, candidate_id: str) -> SourceContextCandidate | None:
        """Return a candidate by id."""
        ...

    async def save_candidate(self, *, candidate: SourceContextCandidate) -> None:
        """Persist candidate state."""
        ...

    async def get_confirmed_fact_by_candidate_id(self, *, candidate_id: str) -> ConfirmedFact | None:
        """Return a promoted fact for idempotent validation decisions."""
        ...

    async def save_confirmed_fact(self, *, confirmed_fact: ConfirmedFact) -> None:
        """Persist an authoritative confirmed fact."""
        ...

    async def save_candidate_with_confirmed_fact(
        self,
        *,
        candidate: SourceContextCandidate,
        confirmed_fact: ConfirmedFact,
    ) -> None:
        """Atomically persist candidate promotion and its confirmed fact."""
        ...

    async def list_candidates(self, *, tenant_id: str) -> list[SourceContextCandidate]:
        """List candidate states for a tenant."""
        ...

    async def list_confirmed_facts(self, *, tenant_id: str) -> list[ConfirmedFact]:
        """List authoritative confirmed facts for a tenant."""
        ...
