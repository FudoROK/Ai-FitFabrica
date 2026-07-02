from __future__ import annotations

import pytest

from src.domain.try_on import TryOnHumanIdentityVerdict
from src.domain.try_on import TryOnHumanIdentityAnalysis
from src.use_cases.try_on.human_identity_policy import HumanIdentityContinuationPolicy


def _analysis_values(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "face_visibility": "fully_visible",
        "body_region_visibility": ["face", "torso", "arms"],
        "preservation_target_count": 3,
        "confidence": 0.94,
        "uncertainty_level": "low",
        "subject_count": 1,
        "crop_quality": "full_body",
        "try_on_body_coverage": "sufficient",
        "occlusion_risk": "low",
        "required_regions_missing": [],
    }
    values.update(overrides)
    return values


def test_human_identity_policy_allows_complete_high_confidence_analysis() -> None:
    decision = HumanIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(**_analysis_values())

    assert decision.verdict == TryOnHumanIdentityVerdict.ALLOWED
    assert decision.rejection_reasons == []


def test_human_identity_policy_allows_complete_v2_analysis_without_advisory_targets() -> None:
    decision = HumanIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(
        **_analysis_values(preservation_target_count=0)
    )

    assert decision.verdict == TryOnHumanIdentityVerdict.ALLOWED
    assert decision.rejection_reasons == []


@pytest.mark.parametrize(
    ("overrides", "expected_reason"),
    [
        ({"face_visibility": "not_visible"}, "face_not_visible"),
        ({"body_region_visibility": []}, "body_regions_not_visible"),
        ({"confidence": 0.79}, "confidence_below_minimum"),
        ({"uncertainty_level": "high"}, "uncertainty_too_high"),
        ({"face_visibility": "partially_visible"}, "face_not_fully_visible"),
        ({"face_visibility": "occluded"}, "face_not_fully_visible"),
        ({"subject_count": 2}, "multiple_subjects_detected"),
        ({"subject_count": 0}, "no_human_subject_detected"),
        ({"crop_quality": "headshot"}, "tight_headshot_crop"),
        ({"crop_quality": "extreme_crop"}, "tight_headshot_crop"),
        ({"try_on_body_coverage": "insufficient"}, "insufficient_body_coverage"),
        ({"occlusion_risk": "high"}, "human_occlusion_risk_too_high"),
        ({"required_regions_missing": ["torso", "legs"]}, "required_regions_missing"),
    ],
)
def test_human_identity_policy_blocks_unsuitable_analysis(
    overrides: dict[str, object],
    expected_reason: str,
) -> None:
    decision = HumanIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(**_analysis_values(**overrides))

    assert decision.verdict == TryOnHumanIdentityVerdict.BLOCKED
    assert expected_reason in decision.rejection_reasons


@pytest.mark.parametrize(
    ("asset_case", "overrides", "expected_reasons"),
    [
        (
            "cropped_face_only.jpg",
            {
                "crop_quality": "headshot",
                "try_on_body_coverage": "insufficient",
                "required_regions_missing": ["torso", "arms", "legs"],
            },
            {"tight_headshot_crop", "insufficient_body_coverage", "required_regions_missing"},
        ),
        (
            "face_hidden.jpg",
            {
                "face_visibility": "partially_visible",
                "occlusion_risk": "high",
                "required_regions_missing": ["full_face"],
            },
            {"face_not_fully_visible", "human_occlusion_risk_too_high", "required_regions_missing"},
        ),
        (
            "multiple_people.jpg",
            {"subject_count": 4},
            {"multiple_subjects_detected"},
        ),
    ],
)
def test_human_identity_policy_blocks_acceptance_false_passes(
    asset_case: str,
    overrides: dict[str, object],
    expected_reasons: set[str],
) -> None:
    decision = HumanIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(**_analysis_values(**overrides))

    assert decision.verdict == TryOnHumanIdentityVerdict.BLOCKED, asset_case
    assert expected_reasons.issubset(set(decision.rejection_reasons))


@pytest.mark.parametrize(
    ("asset_case", "overrides", "expected_verdict", "expected_reasons"),
    [
        ("good_front.jpg", {"preservation_target_count": 0}, TryOnHumanIdentityVerdict.ALLOWED, set()),
        ("side_pose.jpg", {}, TryOnHumanIdentityVerdict.ALLOWED, set()),
        (
            "blurry_dark.jpg",
            {"face_visibility": "partially_visible", "confidence": 0.3, "uncertainty_level": "high"},
            TryOnHumanIdentityVerdict.BLOCKED,
            {"face_not_fully_visible", "confidence_below_minimum", "uncertainty_too_high"},
        ),
        (
            "multiple_people.jpg",
            {"subject_count": 10, "try_on_body_coverage": "insufficient"},
            TryOnHumanIdentityVerdict.BLOCKED,
            {"multiple_subjects_detected", "insufficient_body_coverage"},
        ),
        (
            "multiple_people_masks.jpg",
            {"subject_count": 2, "face_visibility": "partially_visible", "occlusion_risk": "high"},
            TryOnHumanIdentityVerdict.BLOCKED,
            {"multiple_subjects_detected", "face_not_fully_visible", "human_occlusion_risk_too_high"},
        ),
        (
            "not_human.jpg",
            {
                "subject_count": 0,
                "face_visibility": "not_visible",
                "body_region_visibility": [],
                "crop_quality": "extreme_crop",
                "try_on_body_coverage": "insufficient",
            },
            TryOnHumanIdentityVerdict.BLOCKED,
            {
                "no_human_subject_detected",
                "face_not_visible",
                "body_regions_not_visible",
                "tight_headshot_crop",
                "insufficient_body_coverage",
            },
        ),
        (
            "cropped_face_only.jpg",
            {
                "crop_quality": "headshot",
                "try_on_body_coverage": "insufficient",
                "required_regions_missing": ["torso", "arms", "legs"],
            },
            TryOnHumanIdentityVerdict.BLOCKED,
            {"tight_headshot_crop", "insufficient_body_coverage", "required_regions_missing"},
        ),
        (
            "face_hidden.jpg",
            {
                "face_visibility": "partially_visible",
                "occlusion_risk": "high",
                "required_regions_missing": ["full_face"],
            },
            TryOnHumanIdentityVerdict.BLOCKED,
            {"face_not_fully_visible", "human_occlusion_risk_too_high", "required_regions_missing"},
        ),
    ],
)
def test_human_identity_policy_acceptance_matrix_for_current_assets(
    asset_case: str,
    overrides: dict[str, object],
    expected_verdict: TryOnHumanIdentityVerdict,
    expected_reasons: set[str],
) -> None:
    decision = HumanIdentityContinuationPolicy(minimum_confidence=0.8).evaluate(**_analysis_values(**overrides))

    assert decision.verdict == expected_verdict, asset_case
    assert expected_reasons.issubset(set(decision.rejection_reasons)), asset_case


def test_human_identity_domain_loads_legacy_persisted_analysis_without_new_v2_fields() -> None:
    analysis = TryOnHumanIdentityAnalysis.model_validate(
        {
            "invocation_id": "legacy-invocation",
            "prompt_version": "human_identity.v1",
            "contract_version": "human_identity.contract.v1",
            "face_visibility": "fully_visible",
            "pose_summary": "Legacy front-facing pose.",
            "body_region_visibility": ["face", "torso"],
            "preservation_targets": [],
            "confidence": 0.9,
            "limitations": [],
            "evidence": [],
            "uncertainty_level": "low",
            "unknowns": [],
            "verdict": "allowed",
            "rejection_reasons": [],
        }
    )

    assert analysis.subject_count == 1
    assert analysis.try_on_body_coverage == "partial"
