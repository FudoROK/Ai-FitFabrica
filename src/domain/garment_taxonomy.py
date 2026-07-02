"""Backend-owned garment taxonomy and wear-control domain models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from re import sub
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _normalize_code(value: str) -> str:
    """Normalize user/model-proposed labels into stable taxonomy codes."""
    normalized = sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    if not normalized:
        raise ValueError("code must not be empty")
    return normalized


class GarmentWearControlRiskLevel(StrEnum):
    """Risk tier for applying one way-of-wearing control."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class GarmentTaxonomyCandidateStatus(StrEnum):
    """Human-review lifecycle for AI-proposed taxonomy candidates."""

    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"
    NEEDS_MORE_EXAMPLES = "needs_more_examples"


class GarmentTaxonomyAuditAction(StrEnum):
    """Audited mutation types for taxonomy governance."""

    CREATE_CANDIDATE = "create_candidate"
    APPROVE_CANDIDATE = "approve_candidate"
    REJECT_CANDIDATE = "reject_candidate"
    MERGE_CANDIDATE = "merge_candidate"
    RENAME_AND_APPROVE_CANDIDATE = "rename_and_approve_candidate"
    MARK_NEEDS_MORE_EXAMPLES = "mark_needs_more_examples"


class GarmentTaxonomyItem(BaseModel):
    """One approved production garment type or category."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1)
    category: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    parent_code: str | None = None
    description: str | None = None
    active: bool = True
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    @field_validator("code", "category", "parent_code", mode="before")
    @classmethod
    def _normalize_optional_code(cls, value: object) -> str | None:
        if value is None:
            return None
        return _normalize_code(str(value))


class GarmentWearControl(BaseModel):
    """One approved way a garment can be worn for a taxonomy item or category."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    control_code: str = Field(min_length=1)
    display_name: str = Field(min_length=1)
    instruction_template: str = Field(min_length=1)
    taxonomy_item_code: str | None = None
    parent_category_code: str | None = None
    description: str | None = None
    risk_level: GarmentWearControlRiskLevel = GarmentWearControlRiskLevel.LOW
    default_for_auto: bool = False
    active: bool = True
    version: int = Field(default=1, ge=1)

    @field_validator("control_code", "taxonomy_item_code", "parent_category_code", mode="before")
    @classmethod
    def _normalize_optional_code(cls, value: object) -> str | None:
        if value is None:
            return None
        return _normalize_code(str(value))

    @model_validator(mode="after")
    def _require_scope(self) -> "GarmentWearControl":
        if not self.taxonomy_item_code and not self.parent_category_code:
            raise ValueError("wear control requires taxonomy_item_code or parent_category_code")
        return self


class GarmentTaxonomyCandidate(BaseModel):
    """AI-proposed garment taxonomy item waiting for human review."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    proposed_code: str = Field(min_length=1)
    proposed_display_name: str = Field(min_length=1)
    proposed_category: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    agent_reasoning_summary: str = Field(min_length=1)
    proposed_parent_code: str | None = None
    proposed_controls: list[str] = Field(default_factory=list)
    source_job_ids: list[str] = Field(default_factory=list)
    examples_count: int = Field(default=1, ge=0)
    status: GarmentTaxonomyCandidateStatus = GarmentTaxonomyCandidateStatus.PENDING_REVIEW
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_reason: str | None = None
    approved_catalog_item_code: str | None = None
    created_at: datetime = Field(default_factory=_utc_now)

    @field_validator(
        "proposed_code",
        "proposed_category",
        "proposed_parent_code",
        "approved_catalog_item_code",
        mode="before",
    )
    @classmethod
    def _normalize_optional_code(cls, value: object) -> str | None:
        if value is None:
            return None
        return _normalize_code(str(value))

    @field_validator("proposed_controls", mode="before")
    @classmethod
    def _normalize_control_codes(cls, value: object) -> list[str]:
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise ValueError("proposed_controls must be a list")
        return [_normalize_code(str(item)) for item in value if str(item).strip()]

    def approve(self, *, actor_id: str, approved_catalog_item_code: str) -> "GarmentTaxonomyCandidate":
        """Return an approved copy after validating human-review requirements."""
        if not actor_id.strip():
            raise ValueError("reviewed_by is required")
        if not approved_catalog_item_code.strip():
            raise ValueError("approved_catalog_item_code is required")
        return self.model_copy(
            update={
                "status": GarmentTaxonomyCandidateStatus.APPROVED,
                "reviewed_by": actor_id.strip(),
                "reviewed_at": _utc_now(),
                "approved_catalog_item_code": _normalize_code(approved_catalog_item_code),
            }
        )

    def reject(self, *, actor_id: str, review_reason: str) -> "GarmentTaxonomyCandidate":
        """Return a rejected copy after validating human-review requirements."""
        if not actor_id.strip():
            raise ValueError("reviewed_by is required")
        if not review_reason.strip():
            raise ValueError("review_reason is required")
        return self.model_copy(
            update={
                "status": GarmentTaxonomyCandidateStatus.REJECTED,
                "reviewed_by": actor_id.strip(),
                "reviewed_at": _utc_now(),
                "review_reason": review_reason.strip(),
            }
        )


class GarmentTaxonomyAuditEvent(BaseModel):
    """Audit record for every taxonomy review mutation."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(default_factory=lambda: uuid4().hex, min_length=1)
    actor_id: str = Field(min_length=1)
    action: GarmentTaxonomyAuditAction
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    before_json: dict[str, object] = Field(default_factory=dict)
    after_json: dict[str, object] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utc_now)
