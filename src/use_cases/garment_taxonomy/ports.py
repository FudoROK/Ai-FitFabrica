"""Ports for garment taxonomy persistence."""

from __future__ import annotations

from typing import Protocol

from src.domain.garment_taxonomy import (
    GarmentTaxonomyAuditEvent,
    GarmentTaxonomyCandidate,
    GarmentTaxonomyCandidateStatus,
    GarmentTaxonomyItem,
    GarmentWearControl,
)


class GarmentTaxonomyRepositoryPort(Protocol):
    """Persistence boundary for garment taxonomy catalog and candidates."""

    async def get_item_by_code(self, code: str) -> GarmentTaxonomyItem | None:
        """Return one approved taxonomy item by normalized code."""
        ...

    async def list_controls_for_item_or_parent(self, code: str) -> list[GarmentWearControl]:
        """Return active controls scoped to the item or its parent category."""
        ...

    async def save_candidate(self, candidate: GarmentTaxonomyCandidate) -> GarmentTaxonomyCandidate:
        """Persist one AI-proposed taxonomy candidate for human review."""
        ...

    async def list_candidates(
        self,
        status: GarmentTaxonomyCandidateStatus | None = None,
    ) -> list[GarmentTaxonomyCandidate]:
        """Return taxonomy candidates, optionally filtered by review status."""
        ...

    async def get_candidate(self, candidate_id: str) -> GarmentTaxonomyCandidate | None:
        """Return one taxonomy candidate by id."""
        ...

    async def update_candidate(self, candidate: GarmentTaxonomyCandidate) -> GarmentTaxonomyCandidate:
        """Persist one reviewed taxonomy candidate state."""
        ...

    async def upsert_item(self, item: GarmentTaxonomyItem) -> GarmentTaxonomyItem:
        """Insert or update one approved taxonomy item."""
        ...

    async def write_audit_event(self, event: GarmentTaxonomyAuditEvent) -> GarmentTaxonomyAuditEvent:
        """Persist one admin taxonomy audit event."""
        ...
