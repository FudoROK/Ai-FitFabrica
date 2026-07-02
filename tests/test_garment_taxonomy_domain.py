import pytest
from pydantic import ValidationError

from src.domain.garment_taxonomy import (
    GarmentTaxonomyAuditAction,
    GarmentTaxonomyAuditEvent,
    GarmentTaxonomyCandidate,
    GarmentTaxonomyCandidateStatus,
    GarmentTaxonomyItem,
    GarmentWearControl,
    GarmentWearControlRiskLevel,
)


def test_taxonomy_item_normalizes_code_and_category() -> None:
    item = GarmentTaxonomyItem(
        code=" Long Sleeve Shirt ",
        category=" Tops ",
        display_name="Long Sleeve Shirt",
    )

    assert item.code == "long_sleeve_shirt"
    assert item.category == "tops"
    assert item.active is True
    assert item.version == 1


def test_wear_control_requires_catalog_scope() -> None:
    with pytest.raises(ValidationError):
        GarmentWearControl(
            control_code="untucked",
            display_name="Навыпуск",
            instruction_template="Keep the hem visible over the waistband.",
        )


def test_wear_control_normalizes_codes_and_preserves_risk() -> None:
    control = GarmentWearControl(
        taxonomy_item_code="shirt",
        control_code=" Half Tucked ",
        display_name="Частично заправить",
        instruction_template="Tuck only the front section while preserving garment details.",
        risk_level=GarmentWearControlRiskLevel.MEDIUM,
    )

    assert control.taxonomy_item_code == "shirt"
    assert control.control_code == "half_tucked"
    assert control.risk_level == GarmentWearControlRiskLevel.MEDIUM


def test_candidate_defaults_to_pending_review_without_mutating_catalog() -> None:
    candidate = GarmentTaxonomyCandidate(
        proposed_code="Kimono Jacket",
        proposed_display_name="Kimono jacket",
        proposed_category="Outerwear",
        proposed_controls=["open", "draped", "unknown control"],
        source_job_ids=["try_on_1", "try_on_2"],
        confidence=0.72,
        agent_reasoning_summary="Looks like a lightweight open outerwear layer.",
    )

    assert candidate.proposed_code == "kimono_jacket"
    assert candidate.proposed_category == "outerwear"
    assert candidate.status == GarmentTaxonomyCandidateStatus.PENDING_REVIEW
    assert candidate.approved_catalog_item_code is None


def test_approved_candidate_requires_actor_and_catalog_code() -> None:
    candidate = GarmentTaxonomyCandidate(
        proposed_code="robe coat",
        proposed_display_name="Robe coat",
        proposed_category="outerwear",
        proposed_controls=["open", "belted"],
        confidence=0.81,
        agent_reasoning_summary="Long coat with robe-like belt.",
    )

    with pytest.raises(ValueError, match="reviewed_by"):
        candidate.approve(actor_id="", approved_catalog_item_code="robe_coat")

    with pytest.raises(ValueError, match="approved_catalog_item_code"):
        candidate.approve(actor_id="admin-1", approved_catalog_item_code="")

    approved = candidate.approve(actor_id="admin-1", approved_catalog_item_code="robe coat")

    assert approved.status == GarmentTaxonomyCandidateStatus.APPROVED
    assert approved.reviewed_by == "admin-1"
    assert approved.approved_catalog_item_code == "robe_coat"


def test_rejected_candidate_requires_actor_and_reason() -> None:
    candidate = GarmentTaxonomyCandidate(
        proposed_code="random fabric",
        proposed_display_name="Random fabric",
        proposed_category="unknown",
        proposed_controls=[],
        confidence=0.4,
        agent_reasoning_summary="Unclear object.",
    )

    with pytest.raises(ValueError, match="review_reason"):
        candidate.reject(actor_id="admin-1", review_reason="")

    rejected = candidate.reject(actor_id="admin-1", review_reason="Not a garment type.")

    assert rejected.status == GarmentTaxonomyCandidateStatus.REJECTED
    assert rejected.reviewed_by == "admin-1"
    assert rejected.review_reason == "Not a garment type."


def test_audit_event_requires_actor_for_mutations() -> None:
    with pytest.raises(ValidationError):
        GarmentTaxonomyAuditEvent(
            actor_id="",
            action=GarmentTaxonomyAuditAction.APPROVE_CANDIDATE,
            entity_type="candidate",
            entity_id="candidate-1",
            before_json={},
            after_json={"status": "approved"},
        )

