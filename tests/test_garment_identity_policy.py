from __future__ import annotations

import pytest

from src.domain.garment_identity import GarmentIdentityVerdict, GarmentIdentityWorkflowMode
from src.use_cases.garment_identity_policy import GarmentIdentityContinuationPolicy


def _analysis_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "workflow_mode": GarmentIdentityWorkflowMode.PRODUCT_CARD,
        "garment_count": 1,
        "garment_visibility": "fully_visible",
        "crop_quality": "full_garment",
        "try_on_garment_coverage": "sufficient",
        "product_card_coverage": "sufficient",
        "occlusion_risk": "low",
        "required_regions_missing": [],
        "ambiguous_target": False,
        "confidence": 0.92,
        "uncertainty_level": "low",
    }
    values.update(overrides)
    return values


def test_garment_identity_policy_allows_complete_single_garment() -> None:
    decision = GarmentIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(**_analysis_values())

    assert decision.verdict == GarmentIdentityVerdict.ALLOWED
    assert decision.rejection_reasons == []


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"garment_count": 0}, "no_garment_detected"),
        ({"garment_count": 2, "ambiguous_target": False}, "multiple_garments_detected"),
        ({"garment_count": 2, "ambiguous_target": True}, "ambiguous_target_garment"),
        ({"garment_visibility": "partially_visible"}, "garment_not_sufficiently_visible"),
        ({"crop_quality": "major_crop"}, "garment_crop_too_tight"),
        ({"occlusion_risk": "high"}, "garment_occlusion_risk_too_high"),
        ({"required_regions_missing": ["front_closure"]}, "required_garment_regions_missing"),
        ({"confidence": 0.4}, "confidence_below_minimum"),
        ({"uncertainty_level": "high"}, "uncertainty_too_high"),
    ],
)
def test_garment_identity_policy_blocks_unsafe_analysis(overrides: dict[str, object], reason: str) -> None:
    decision = GarmentIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(**_analysis_values(**overrides))

    assert decision.verdict == GarmentIdentityVerdict.BLOCKED
    assert reason in decision.rejection_reasons


def test_garment_identity_policy_requires_try_on_coverage_for_try_on_mode() -> None:
    decision = GarmentIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(
        **_analysis_values(
            workflow_mode=GarmentIdentityWorkflowMode.TRY_ON,
            try_on_garment_coverage="partial",
            product_card_coverage="sufficient",
        )
    )

    assert decision.verdict == GarmentIdentityVerdict.BLOCKED
    assert "insufficient_try_on_garment_coverage" in decision.rejection_reasons


def test_garment_identity_policy_requires_product_card_coverage_for_product_card_mode() -> None:
    decision = GarmentIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(
        **_analysis_values(
            workflow_mode=GarmentIdentityWorkflowMode.PRODUCT_CARD,
            try_on_garment_coverage="sufficient",
            product_card_coverage="partial",
        )
    )

    assert decision.verdict == GarmentIdentityVerdict.BLOCKED
    assert "insufficient_product_card_coverage" in decision.rejection_reasons
