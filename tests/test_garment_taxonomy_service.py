from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from src.domain.garment_taxonomy import (
    GarmentTaxonomyCandidate,
    GarmentTaxonomyCandidateStatus,
    GarmentTaxonomyItem,
    GarmentTaxonomyAuditEvent,
    GarmentWearControl,
)
from src.use_cases.garment_taxonomy.service import (
    GarmentTaxonomyService,
    UnknownGarmentTaxonomyInput,
)


@dataclass
class _RepositoryStub:
    items: dict[str, GarmentTaxonomyItem] = field(default_factory=dict)
    controls: list[GarmentWearControl] = field(default_factory=list)
    candidates: list[GarmentTaxonomyCandidate] = field(default_factory=list)
    audit_events: list[GarmentTaxonomyAuditEvent] = field(default_factory=list)

    async def get_item_by_code(self, code: str) -> GarmentTaxonomyItem | None:
        return self.items.get(code)

    async def list_controls_for_item_or_parent(self, code: str) -> list[GarmentWearControl]:
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
        self.candidates.append(candidate)
        return candidate

    async def list_candidates(
        self,
        status: GarmentTaxonomyCandidateStatus | None = None,
    ) -> list[GarmentTaxonomyCandidate]:
        if status is None:
            return list(self.candidates)
        return [candidate for candidate in self.candidates if candidate.status == status]

    async def get_candidate(self, candidate_id: str) -> GarmentTaxonomyCandidate | None:
        return next((candidate for candidate in self.candidates if candidate.id == candidate_id), None)

    async def update_candidate(self, candidate: GarmentTaxonomyCandidate) -> GarmentTaxonomyCandidate:
        self.candidates = [
            candidate if existing.id == candidate.id else existing
            for existing in self.candidates
        ]
        return candidate

    async def upsert_item(self, item: GarmentTaxonomyItem) -> GarmentTaxonomyItem:
        self.items[item.code] = item
        return item

    async def write_audit_event(self, event: GarmentTaxonomyAuditEvent) -> GarmentTaxonomyAuditEvent:
        self.audit_events.append(event)
        return event


def _repository() -> _RepositoryStub:
    return _RepositoryStub(
        items={
            "shirt": GarmentTaxonomyItem(
                code="shirt",
                category="tops",
                display_name="Shirt",
            )
        },
        controls=[
            GarmentWearControl(
                taxonomy_item_code="shirt",
                control_code="untucked",
                display_name="Навыпуск",
                instruction_template="Keep the shirt hem visible over the waistband.",
                default_for_auto=True,
            ),
            GarmentWearControl(
                taxonomy_item_code="shirt",
                control_code="tucked",
                display_name="Заправить",
                instruction_template="Tuck the shirt into the waistband.",
            ),
            GarmentWearControl(
                parent_category_code="tops",
                control_code="relaxed_fit",
                display_name="Свободнее",
                instruction_template="Keep the garment fit relaxed.",
            ),
            GarmentWearControl(
                taxonomy_item_code="shirt",
                control_code="deprecated_control",
                display_name="Deprecated",
                instruction_template="Do not use.",
                active=False,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_known_garment_type_returns_item_and_allowed_controls() -> None:
    service = GarmentTaxonomyService(repository=_repository())

    result = await service.resolve_available_controls(garment_type=" Shirt ")

    assert result.taxonomy_item.code == "shirt"
    assert [control.control_code for control in result.available_controls] == [
        "untucked",
        "tucked",
        "relaxed_fit",
    ]
    assert result.created_candidate is None


@pytest.mark.asyncio
async def test_known_garment_alias_resolves_to_baseline_catalog_item() -> None:
    service = GarmentTaxonomyService(repository=_repository())

    result = await service.resolve_available_controls(garment_type="button-up shirt")

    assert result.taxonomy_item is not None
    assert result.taxonomy_item.code == "shirt"
    assert [control.control_code for control in result.available_controls] == [
        "untucked",
        "tucked",
        "relaxed_fit",
    ]
    assert result.created_candidate is None


@pytest.mark.asyncio
async def test_auto_control_resolves_to_backend_default() -> None:
    service = GarmentTaxonomyService(repository=_repository())

    result = await service.resolve_selected_control(garment_type="shirt", selected_control_code="auto")

    assert result.selected_control.control_code == "untucked"
    assert result.requested_control_code == "auto"
    assert result.resolved_by == "backend_auto_default"


@pytest.mark.asyncio
async def test_invalid_selected_control_is_rejected() -> None:
    service = GarmentTaxonomyService(repository=_repository())

    with pytest.raises(ValueError, match="not allowed"):
        await service.resolve_selected_control(garment_type="shirt", selected_control_code="magic_style")


@pytest.mark.asyncio
async def test_unknown_garment_type_creates_candidate_without_mutating_catalog() -> None:
    repository = _repository()
    service = GarmentTaxonomyService(repository=repository)

    result = await service.resolve_available_controls(
        garment_type="Kimono Jacket",
        unknown_input=UnknownGarmentTaxonomyInput(
            proposed_display_name="Kimono jacket",
            proposed_category="outerwear",
            proposed_controls=["open", "draped"],
            source_job_id="try_on_123",
            confidence=0.74,
            agent_reasoning_summary="Open lightweight outerwear layer.",
        ),
    )

    assert result.taxonomy_item is None
    assert result.available_controls == []
    assert result.created_candidate is not None
    assert result.created_candidate.status == GarmentTaxonomyCandidateStatus.PENDING_REVIEW
    assert result.created_candidate.proposed_code == "kimono_jacket"
    assert result.created_candidate.source_job_ids == ["try_on_123"]
    assert "kimono_jacket" not in repository.items
    assert len(repository.candidates) == 1


@pytest.mark.asyncio
async def test_unknown_control_candidates_are_filtered_against_catalog() -> None:
    service = GarmentTaxonomyService(repository=_repository())

    result = await service.filter_agent_control_candidates(
        garment_type="shirt",
        proposed_control_codes=["untucked", "magic style", "relaxed_fit"],
    )

    assert [control.control_code for control in result] == ["untucked", "relaxed_fit"]


@pytest.mark.asyncio
async def test_admin_approve_candidate_creates_catalog_item_and_audit_event() -> None:
    repository = _repository()
    candidate = GarmentTaxonomyCandidate(
        proposed_code="kimono jacket",
        proposed_display_name="Kimono jacket",
        proposed_category="outerwear",
        confidence=0.74,
        agent_reasoning_summary="Open lightweight outerwear layer.",
    )
    repository.candidates.append(candidate)
    service = GarmentTaxonomyService(repository=repository)

    result = await service.approve_candidate(candidate_id=candidate.id, actor_id="admin-1")

    assert result.status == GarmentTaxonomyCandidateStatus.APPROVED
    assert result.approved_catalog_item_code == "kimono_jacket"
    assert repository.items["kimono_jacket"].display_name == "Kimono jacket"
    assert repository.audit_events[-1].action.value == "approve_candidate"
    assert repository.audit_events[-1].actor_id == "admin-1"


@pytest.mark.asyncio
async def test_admin_reject_candidate_records_reason_and_audit_event() -> None:
    repository = _repository()
    candidate = GarmentTaxonomyCandidate(
        proposed_code="kimono jacket",
        proposed_display_name="Kimono jacket",
        proposed_category="outerwear",
        confidence=0.74,
        agent_reasoning_summary="Open lightweight outerwear layer.",
    )
    repository.candidates.append(candidate)
    service = GarmentTaxonomyService(repository=repository)

    result = await service.reject_candidate(
        candidate_id=candidate.id,
        actor_id="admin-1",
        review_reason="Too broad for the catalog.",
    )

    assert result.status == GarmentTaxonomyCandidateStatus.REJECTED
    assert result.review_reason == "Too broad for the catalog."
    assert "kimono_jacket" not in repository.items
    assert repository.audit_events[-1].action.value == "reject_candidate"


@pytest.mark.asyncio
async def test_admin_merge_candidate_requires_existing_target() -> None:
    repository = _repository()
    candidate = GarmentTaxonomyCandidate(
        proposed_code="overshirt",
        proposed_display_name="Overshirt",
        proposed_category="tops",
        confidence=0.8,
        agent_reasoning_summary="Looks like an existing shirt subtype.",
    )
    repository.candidates.append(candidate)
    service = GarmentTaxonomyService(repository=repository)

    with pytest.raises(ValueError, match="target taxonomy item"):
        await service.merge_candidate(
            candidate_id=candidate.id,
            actor_id="admin-1",
            target_catalog_item_code="missing",
        )

    result = await service.merge_candidate(
        candidate_id=candidate.id,
        actor_id="admin-1",
        target_catalog_item_code="shirt",
    )

    assert result.status == GarmentTaxonomyCandidateStatus.MERGED
    assert result.approved_catalog_item_code == "shirt"
    assert repository.audit_events[-1].action.value == "merge_candidate"


@pytest.mark.asyncio
async def test_admin_rename_and_approve_candidate_creates_catalog_item_and_audit_event() -> None:
    repository = _repository()
    candidate = GarmentTaxonomyCandidate(
        proposed_code="kimono jacket",
        proposed_display_name="Kimono jacket",
        proposed_category="outerwear",
        confidence=0.74,
        agent_reasoning_summary="Open lightweight outerwear layer.",
    )
    repository.candidates.append(candidate)
    service = GarmentTaxonomyService(repository=repository)

    result = await service.rename_and_approve_candidate(
        candidate_id=candidate.id,
        actor_id="admin-1",
        approved_catalog_item_code="kimono_outer_layer",
        approved_display_name="Kimono Outer Layer",
    )

    assert result.status == GarmentTaxonomyCandidateStatus.APPROVED
    assert result.approved_catalog_item_code == "kimono_outer_layer"
    assert repository.items["kimono_outer_layer"].display_name == "Kimono Outer Layer"
    assert repository.audit_events[-1].action.value == "rename_and_approve_candidate"
    assert repository.audit_events[-1].actor_id == "admin-1"
