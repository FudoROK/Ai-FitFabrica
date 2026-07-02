from __future__ import annotations

from pathlib import Path

import pytest

from scripts.quality_verifier_live_acceptance import (
    REQUIRED_CASES,
    REQUIRED_FILES,
    acceptable_decisions_for,
    collect_acceptance_cases,
    expected_decision_for,
    quality_verifier_approved_constraints,
    wear_control_constraint_for,
)


def test_quality_verifier_acceptance_requires_canonical_dataset(tmp_path: Path) -> None:
    missing_case = REQUIRED_CASES[0]

    with pytest.raises(ValueError, match=missing_case):
        collect_acceptance_cases(tmp_path)


def test_quality_verifier_acceptance_collects_all_required_cases(tmp_path: Path) -> None:
    for case_name in REQUIRED_CASES:
        case_dir = tmp_path / case_name
        case_dir.mkdir()
        for file_name in REQUIRED_FILES:
            (case_dir / file_name).write_bytes(b"image")

    cases = collect_acceptance_cases(tmp_path)

    assert [case.name for case in cases] == sorted(REQUIRED_CASES)
    assert {case.expected_decision for case in cases} == {"pass", "repair_recommended", "reject"}
    for case in cases:
        assert set(case.files) == set(REQUIRED_FILES)
        constraints = quality_verifier_approved_constraints(case)
        assert any("selected wear control" in item.lower() for item in constraints)
        assert any("wear_control_match" in item for item in constraints)
        assert any("normal collar opening" in item.lower() for item in constraints)
        assert any("buttoned_closed" in item for item in constraints)
        assert any("visible base layer" in item.lower() for item in constraints)


@pytest.mark.parametrize(
    ("case_name", "expected"),
    [
        ("good_generated_result", "pass"),
        ("minor_background_artifact", "repair_recommended"),
        ("minor_color_shift", "reject"),
        ("face_changed", "reject"),
        ("body_pose_changed", "reject"),
        ("wrong_garment", "reject"),
        ("missing_key_garment_detail", "reject"),
        ("severe_anatomy_artifact", "reject"),
    ],
)
def test_quality_verifier_expected_decisions(case_name: str, expected: str) -> None:
    assert expected_decision_for(case_name) == expected


def test_quality_verifier_minor_color_shift_never_accepts_pass() -> None:
    acceptable = acceptable_decisions_for("minor_color_shift")

    assert acceptable == frozenset({"repair_recommended", "reject"})
    assert "pass" not in acceptable


def test_quality_verifier_good_result_requires_pass() -> None:
    assert acceptable_decisions_for("good_generated_result") == frozenset({"pass"})


def test_quality_verifier_case_wear_control_is_explicit() -> None:
    constraint = wear_control_constraint_for("good_generated_result")

    assert "buttoned_closed" in constraint
    assert "explicitly approved" in constraint
    assert "Do not reject the buttoned front" in constraint
