"""In-memory garment taxonomy repository for isolated test and local sandbox runtimes."""

from __future__ import annotations

from dataclasses import dataclass, field

from src.domain.garment_taxonomy import (
    GarmentTaxonomyAuditEvent,
    GarmentTaxonomyCandidate,
    GarmentTaxonomyCandidateStatus,
    GarmentTaxonomyItem,
    GarmentWearControl,
)


@dataclass
class InMemoryGarmentTaxonomyRepository:
    """Non-durable taxonomy repository used only by test/local sandbox runtimes."""

    items: dict[str, GarmentTaxonomyItem] = field(default_factory=dict)
    controls: list[GarmentWearControl] = field(default_factory=list)
    candidates: dict[str, GarmentTaxonomyCandidate] = field(default_factory=dict)
    audit_events: list[GarmentTaxonomyAuditEvent] = field(default_factory=list)

    async def get_item_by_code(self, code: str) -> GarmentTaxonomyItem | None:
        """Return one approved taxonomy item by code."""
        return self.items.get(code)

    async def list_controls_for_item_or_parent(self, code: str) -> list[GarmentWearControl]:
        """Return active controls scoped to the item or its parent category."""
        item = self.items[code]
        return [
            control
            for control in self.controls
            if control.active
            and (
                control.taxonomy_item_code == item.code
                or control.parent_category_code == item.category
            )
        ]

    async def save_candidate(self, candidate: GarmentTaxonomyCandidate) -> GarmentTaxonomyCandidate:
        """Save one proposed taxonomy candidate."""
        self.candidates[candidate.id] = candidate
        return candidate

    async def list_candidates(
        self,
        status: GarmentTaxonomyCandidateStatus | None = None,
    ) -> list[GarmentTaxonomyCandidate]:
        """Return candidates, optionally filtered by status."""
        candidates = list(self.candidates.values())
        if status is None:
            return candidates
        return [candidate for candidate in candidates if candidate.status == status]

    async def get_candidate(self, candidate_id: str) -> GarmentTaxonomyCandidate | None:
        """Return one candidate by id."""
        return self.candidates.get(candidate_id)

    async def update_candidate(self, candidate: GarmentTaxonomyCandidate) -> GarmentTaxonomyCandidate:
        """Persist a reviewed candidate."""
        self.candidates[candidate.id] = candidate
        return candidate

    async def upsert_item(self, item: GarmentTaxonomyItem) -> GarmentTaxonomyItem:
        """Insert or update one approved taxonomy item."""
        self.items[item.code] = item
        return item

    async def write_audit_event(self, event: GarmentTaxonomyAuditEvent) -> GarmentTaxonomyAuditEvent:
        """Record one taxonomy audit event in memory."""
        self.audit_events.append(event)
        return event


def build_test_garment_taxonomy_repository() -> InMemoryGarmentTaxonomyRepository:
    """Return the deterministic taxonomy catalog used by local browser acceptance."""
    return InMemoryGarmentTaxonomyRepository(
        items={
            "test_garment": GarmentTaxonomyItem(
                code="test_garment",
                category="tops",
                display_name="Test garment",
            )
        },
        controls=[
            GarmentWearControl(
                taxonomy_item_code="test_garment",
                control_code="relaxed_drape",
                display_name="Relaxed drape",
                instruction_template="Keep the test garment relaxed and untucked over the base outfit.",
                default_for_auto=True,
            )
        ],
    )
