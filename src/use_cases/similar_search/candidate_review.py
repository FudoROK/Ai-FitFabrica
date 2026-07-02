"""Review workflow for marketplace/open-web discovery candidates."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from src.domain.marketplace_search import (
    MarketplaceDiscoveryCandidate,
    MarketplaceDiscoveryCandidateStatus,
    MarketplaceSourceType,
)


class MarketplaceCandidateRepositoryPort(Protocol):
    """Persistence boundary for review-required marketplace discovery candidates."""

    async def create_candidate(self, candidate: MarketplaceDiscoveryCandidate) -> MarketplaceDiscoveryCandidate:
        """Persist one candidate and return the durable record."""

    async def save_candidates(self, candidates: list[MarketplaceDiscoveryCandidate]) -> list[MarketplaceDiscoveryCandidate]:
        """Persist candidates and return the saved records."""

    async def get_candidate(self, candidate_id: str) -> MarketplaceDiscoveryCandidate | None:
        """Return one candidate by id."""

    async def list_candidates(
        self,
        *,
        status: MarketplaceDiscoveryCandidateStatus | None = None,
        source_type: MarketplaceSourceType | None = None,
        category: str | None = None,
        city: str | None = None,
        workspace_id: str | None = None,
        business_id: str | None = None,
        limit: int = 20,
    ) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates with optional admin review filters."""

    async def list_pending_candidates(self, *, limit: int) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates waiting for admin review."""

    async def update_candidate_status(
        self,
        *,
        candidate_id: str,
        status: MarketplaceDiscoveryCandidateStatus,
        admin_actor_id: str,
        rejection_reason: str | None = None,
    ) -> MarketplaceDiscoveryCandidate:
        """Persist an admin status decision for one candidate."""


class InMemoryMarketplaceCandidateRepository:
    """In-memory candidate repository for tests and local runtime placeholders."""

    def __init__(self) -> None:
        """Create an empty repository."""

        self._records: dict[str, MarketplaceDiscoveryCandidate] = {}

    async def save_candidates(self, candidates: list[MarketplaceDiscoveryCandidate]) -> list[MarketplaceDiscoveryCandidate]:
        """Persist candidates by id, keeping the latest value for duplicates."""

        saved: list[MarketplaceDiscoveryCandidate] = []
        for candidate in candidates:
            saved.append(await self.create_candidate(candidate))
        return saved

    async def create_candidate(self, candidate: MarketplaceDiscoveryCandidate) -> MarketplaceDiscoveryCandidate:
        """Persist one candidate, deduplicating by source URL and scope."""

        for existing in self._records.values():
            if (
                str(existing.source_url) == str(candidate.source_url)
                and existing.workspace_id == candidate.workspace_id
                and existing.business_id == candidate.business_id
            ):
                return existing
        self._records[candidate.candidate_id] = candidate
        return candidate

    async def get_candidate(self, candidate_id: str) -> MarketplaceDiscoveryCandidate | None:
        """Return one candidate by id."""

        return self._records.get(candidate_id)

    async def list_candidates(
        self,
        *,
        status: MarketplaceDiscoveryCandidateStatus | None = None,
        source_type: MarketplaceSourceType | None = None,
        category: str | None = None,
        city: str | None = None,
        workspace_id: str | None = None,
        business_id: str | None = None,
        limit: int = 20,
    ) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates with optional filters."""

        candidates = list(self._records.values())
        if status is not None:
            candidates = [candidate for candidate in candidates if candidate.status is status]
        if source_type is not None:
            candidates = [candidate for candidate in candidates if candidate.source_type is source_type]
        if category is not None:
            candidates = [candidate for candidate in candidates if candidate.category == category]
        if city is not None:
            candidates = [candidate for candidate in candidates if candidate.city == city]
        if workspace_id is not None:
            candidates = [candidate for candidate in candidates if candidate.workspace_id == workspace_id]
        if business_id is not None:
            candidates = [candidate for candidate in candidates if candidate.business_id == business_id]
        return candidates[:limit]

    async def list_pending_candidates(self, *, limit: int) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates that still need review."""

        candidates = [
            candidate
            for candidate in self._records.values()
            if candidate.status
            in {MarketplaceDiscoveryCandidateStatus.PENDING, MarketplaceDiscoveryCandidateStatus.NEEDS_REVIEW}
        ]
        return candidates[:limit]

    async def update_candidate_status(
        self,
        *,
        candidate_id: str,
        status: MarketplaceDiscoveryCandidateStatus,
        admin_actor_id: str,
        rejection_reason: str | None = None,
    ) -> MarketplaceDiscoveryCandidate:
        """Update the status for one candidate."""

        candidate = self._records[candidate_id]
        now = datetime.now(UTC)
        updates: dict[str, object] = {"status": status, "updated_at": now}
        if status is MarketplaceDiscoveryCandidateStatus.APPROVED:
            updates["approved_at"] = now
        if status is MarketplaceDiscoveryCandidateStatus.REJECTED:
            updates["rejected_at"] = now
            updates["rejection_reason"] = rejection_reason
        updated = candidate.model_copy(update=updates)
        self._records[candidate_id] = updated
        return updated


class MarketplaceCandidateReviewService:
    """Backend-owned service for candidate review lifecycle."""

    def __init__(self, *, repository: MarketplaceCandidateRepositoryPort) -> None:
        """Store the persistence boundary."""

        self._repository = repository

    async def save_candidates(self, *, candidates: list[MarketplaceDiscoveryCandidate]) -> list[MarketplaceDiscoveryCandidate]:
        """Save newly discovered candidates for admin review."""

        return await self._repository.save_candidates(candidates)

    async def create_candidate(self, *, candidate: MarketplaceDiscoveryCandidate) -> MarketplaceDiscoveryCandidate:
        """Save one newly discovered candidate for admin review."""

        return await self._repository.create_candidate(candidate)

    async def get_candidate(self, *, candidate_id: str) -> MarketplaceDiscoveryCandidate | None:
        """Return one candidate by id."""

        return await self._repository.get_candidate(candidate_id)

    async def list_candidates(
        self,
        *,
        status: MarketplaceDiscoveryCandidateStatus | None = None,
        source_type: MarketplaceSourceType | None = None,
        category: str | None = None,
        city: str | None = None,
        workspace_id: str | None = None,
        business_id: str | None = None,
        limit: int = 20,
    ) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates with optional admin filters."""

        return await self._repository.list_candidates(
            status=status,
            source_type=source_type,
            category=category,
            city=city,
            workspace_id=workspace_id,
            business_id=business_id,
            limit=limit,
        )

    async def list_pending_candidates(self, *, limit: int) -> list[MarketplaceDiscoveryCandidate]:
        """Return candidates that need admin review."""

        return await self._repository.list_pending_candidates(limit=limit)

    async def approve_candidate(self, *, candidate_id: str, admin_actor_id: str) -> MarketplaceDiscoveryCandidate:
        """Mark one candidate as approved by admin."""

        return await self._repository.update_candidate_status(
            candidate_id=candidate_id,
            status=MarketplaceDiscoveryCandidateStatus.APPROVED,
            admin_actor_id=admin_actor_id,
        )

    async def reject_candidate(
        self,
        *,
        candidate_id: str,
        admin_actor_id: str,
        rejection_reason: str | None = None,
    ) -> MarketplaceDiscoveryCandidate:
        """Mark one candidate as rejected by admin."""

        return await self._repository.update_candidate_status(
            candidate_id=candidate_id,
            status=MarketplaceDiscoveryCandidateStatus.REJECTED,
            admin_actor_id=admin_actor_id,
            rejection_reason=rejection_reason,
        )

    async def archive_candidate(self, *, candidate_id: str, admin_actor_id: str) -> MarketplaceDiscoveryCandidate:
        """Mark one candidate as archived by admin."""

        return await self._repository.update_candidate_status(
            candidate_id=candidate_id,
            status=MarketplaceDiscoveryCandidateStatus.ARCHIVED,
            admin_actor_id=admin_actor_id,
        )
