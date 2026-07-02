"""Application service for garment taxonomy and wear-control resolution."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.garment_taxonomy import (
    GarmentTaxonomyAuditAction,
    GarmentTaxonomyAuditEvent,
    GarmentTaxonomyCandidate,
    GarmentTaxonomyCandidateStatus,
    GarmentTaxonomyItem,
    GarmentWearControl,
)
from src.use_cases.garment_taxonomy.catalog_policy import choose_auto_control, filter_allowed_controls
from src.use_cases.garment_taxonomy.ports import GarmentTaxonomyRepositoryPort


def _normalize_code(value: str) -> str:
    normalized = "_".join(value.strip().lower().replace("-", " ").split())
    if not normalized:
        raise ValueError("code must not be empty")
    return normalized


_GARMENT_CODE_ALIASES = {
    "button_up_shirt": "shirt",
    "button_down_shirt": "shirt",
    "buttoned_shirt": "shirt",
    "collared_shirt": "shirt",
    "dress_shirt": "shirt",
    "tee": "t_shirt",
    "tshirt": "t_shirt",
    "t_shirt": "t_shirt",
    "hooded_sweatshirt": "hoodie",
    "trousers": "pants",
    "denim_jeans": "jeans",
}


def _catalog_lookup_code(value: str) -> str:
    normalized = _normalize_code(value)
    return _GARMENT_CODE_ALIASES.get(normalized, normalized)


class UnknownGarmentTaxonomyInput(BaseModel):
    """Backend-safe data used to create a taxonomy candidate."""

    model_config = ConfigDict(extra="forbid")

    proposed_display_name: str = Field(min_length=1)
    proposed_category: str = Field(min_length=1)
    proposed_controls: list[str] = Field(default_factory=list)
    source_job_id: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    agent_reasoning_summary: str = Field(min_length=1)

    @field_validator("proposed_category", mode="before")
    @classmethod
    def _normalize_category(cls, value: object) -> str:
        return _normalize_code(str(value))


@dataclass(frozen=True)
class AvailableWearControlsResult:
    """Resolved catalog item, controls and optional candidate creation result."""

    taxonomy_item: GarmentTaxonomyItem | None
    available_controls: list[GarmentWearControl]
    created_candidate: GarmentTaxonomyCandidate | None = None


@dataclass(frozen=True)
class SelectedWearControlResult:
    """Validated selected wear-control resolution."""

    requested_control_code: str
    selected_control: GarmentWearControl
    resolved_by: str


class GarmentTaxonomyService:
    """Resolve approved wear controls and capture unknown taxonomy candidates."""

    def __init__(self, *, repository: GarmentTaxonomyRepositoryPort) -> None:
        self._repository = repository

    async def resolve_available_controls(
        self,
        *,
        garment_type: str,
        unknown_input: UnknownGarmentTaxonomyInput | None = None,
    ) -> AvailableWearControlsResult:
        """Return approved controls for a known garment or capture an unknown candidate."""
        garment_code = _catalog_lookup_code(garment_type)
        item = await self._repository.get_item_by_code(garment_code)
        if item is None:
            candidate = await self._capture_unknown_candidate(
                garment_code=garment_code,
                unknown_input=unknown_input,
            )
            return AvailableWearControlsResult(taxonomy_item=None, available_controls=[], created_candidate=candidate)
        controls = await self._repository.list_controls_for_item_or_parent(item.code)
        return AvailableWearControlsResult(taxonomy_item=item, available_controls=controls)

    async def resolve_selected_control(
        self,
        *,
        garment_type: str,
        selected_control_code: str,
    ) -> SelectedWearControlResult:
        """Validate one selected control and resolve backend-owned auto mode."""
        available = await self.resolve_available_controls(garment_type=garment_type)
        controls = available.available_controls
        requested = _normalize_code(selected_control_code)
        if requested == "auto":
            return SelectedWearControlResult(
                requested_control_code="auto",
                selected_control=choose_auto_control(controls),
                resolved_by="backend_auto_default",
            )
        for control in controls:
            if control.control_code == requested:
                return SelectedWearControlResult(
                    requested_control_code=requested,
                    selected_control=control,
                    resolved_by="user_selection",
                )
        raise ValueError(f"wear control {requested!r} is not allowed for garment type {available.taxonomy_item.code if available.taxonomy_item else garment_type!r}")

    async def filter_agent_control_candidates(
        self,
        *,
        garment_type: str,
        proposed_control_codes: list[str],
    ) -> list[GarmentWearControl]:
        """Drop model-proposed controls that are not approved for the garment type."""
        available = await self.resolve_available_controls(garment_type=garment_type)
        return filter_allowed_controls(
            controls=available.available_controls,
            proposed_control_codes=proposed_control_codes,
        )

    async def list_candidates(
        self,
        *,
        status: GarmentTaxonomyCandidateStatus | None = GarmentTaxonomyCandidateStatus.PENDING_REVIEW,
    ) -> list[GarmentTaxonomyCandidate]:
        """Return taxonomy candidates for admin review."""
        return await self._repository.list_candidates(status=status)

    async def approve_candidate(self, *, candidate_id: str, actor_id: str) -> GarmentTaxonomyCandidate:
        """Approve one candidate into the production taxonomy catalog with audit."""
        candidate = await self._require_candidate(candidate_id)
        before_json = candidate.model_dump(mode="json")
        item = GarmentTaxonomyItem(
            code=candidate.proposed_code,
            parent_code=candidate.proposed_parent_code,
            category=candidate.proposed_category,
            display_name=candidate.proposed_display_name,
        )
        reviewed = candidate.approve(actor_id=actor_id, approved_catalog_item_code=item.code)
        await self._repository.upsert_item(item)
        await self._repository.update_candidate(reviewed)
        await self._write_review_audit(
            actor_id=actor_id,
            action=GarmentTaxonomyAuditAction.APPROVE_CANDIDATE,
            before_json=before_json,
            reviewed=reviewed,
        )
        return reviewed

    async def reject_candidate(
        self,
        *,
        candidate_id: str,
        actor_id: str,
        review_reason: str,
    ) -> GarmentTaxonomyCandidate:
        """Reject one candidate with an explicit admin reason and audit."""
        candidate = await self._require_candidate(candidate_id)
        before_json = candidate.model_dump(mode="json")
        reviewed = candidate.reject(actor_id=actor_id, review_reason=review_reason)
        await self._repository.update_candidate(reviewed)
        await self._write_review_audit(
            actor_id=actor_id,
            action=GarmentTaxonomyAuditAction.REJECT_CANDIDATE,
            before_json=before_json,
            reviewed=reviewed,
        )
        return reviewed

    async def merge_candidate(
        self,
        *,
        candidate_id: str,
        actor_id: str,
        target_catalog_item_code: str,
    ) -> GarmentTaxonomyCandidate:
        """Merge one candidate into an existing taxonomy item with audit."""
        target_code = _normalize_code(target_catalog_item_code)
        target_item = await self._repository.get_item_by_code(target_code)
        if target_item is None:
            raise ValueError(f"target taxonomy item {target_code!r} does not exist")
        candidate = await self._require_candidate(candidate_id)
        before_json = candidate.model_dump(mode="json")
        reviewed = candidate.model_copy(
            update={
                "status": GarmentTaxonomyCandidateStatus.MERGED,
                "reviewed_by": actor_id.strip(),
                "reviewed_at": datetime.now(timezone.utc),
                "approved_catalog_item_code": target_item.code,
            }
        )
        await self._repository.update_candidate(reviewed)
        await self._write_review_audit(
            actor_id=actor_id,
            action=GarmentTaxonomyAuditAction.MERGE_CANDIDATE,
            before_json=before_json,
            reviewed=reviewed,
        )
        return reviewed

    async def rename_and_approve_candidate(
        self,
        *,
        candidate_id: str,
        actor_id: str,
        approved_catalog_item_code: str,
        approved_display_name: str,
    ) -> GarmentTaxonomyCandidate:
        """Approve one candidate under an explicit admin-selected catalog code and label."""
        target_code = _normalize_code(approved_catalog_item_code)
        if not actor_id.strip():
            raise ValueError("actor_id is required")
        if not approved_display_name.strip():
            raise ValueError("approved_display_name is required")
        candidate = await self._require_candidate(candidate_id)
        before_json = candidate.model_dump(mode="json")
        item = GarmentTaxonomyItem(
            code=target_code,
            parent_code=candidate.proposed_parent_code,
            category=candidate.proposed_category,
            display_name=approved_display_name.strip(),
        )
        reviewed = candidate.model_copy(
            update={
                "status": GarmentTaxonomyCandidateStatus.APPROVED,
                "reviewed_by": actor_id.strip(),
                "reviewed_at": datetime.now(timezone.utc),
                "approved_catalog_item_code": item.code,
            }
        )
        await self._repository.upsert_item(item)
        await self._repository.update_candidate(reviewed)
        await self._write_review_audit(
            actor_id=actor_id,
            action=GarmentTaxonomyAuditAction.RENAME_AND_APPROVE_CANDIDATE,
            before_json=before_json,
            reviewed=reviewed,
        )
        return reviewed

    async def _capture_unknown_candidate(
        self,
        *,
        garment_code: str,
        unknown_input: UnknownGarmentTaxonomyInput | None,
    ) -> GarmentTaxonomyCandidate | None:
        if unknown_input is None:
            return None
        candidate = GarmentTaxonomyCandidate(
            proposed_code=garment_code,
            proposed_display_name=unknown_input.proposed_display_name,
            proposed_category=unknown_input.proposed_category,
            proposed_controls=unknown_input.proposed_controls,
            source_job_ids=[unknown_input.source_job_id] if unknown_input.source_job_id else [],
            confidence=unknown_input.confidence,
            agent_reasoning_summary=unknown_input.agent_reasoning_summary,
        )
        return await self._repository.save_candidate(candidate)

    async def _require_candidate(self, candidate_id: str) -> GarmentTaxonomyCandidate:
        candidate = await self._repository.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError(f"taxonomy candidate {candidate_id!r} was not found")
        return candidate

    async def _write_review_audit(
        self,
        *,
        actor_id: str,
        action: GarmentTaxonomyAuditAction,
        before_json: dict[str, object],
        reviewed: GarmentTaxonomyCandidate,
    ) -> None:
        await self._repository.write_audit_event(
            GarmentTaxonomyAuditEvent(
                actor_id=actor_id.strip(),
                action=action,
                entity_type="garment_taxonomy_candidate",
                entity_id=reviewed.id,
                before_json=before_json,
                after_json=reviewed.model_dump(mode="json"),
            )
        )
