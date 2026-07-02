from __future__ import annotations

from scripts.try_on_instruction_live_acceptance import REQUIRED_CASES, build_acceptance_cases, expected_decision_for


def test_try_on_instruction_acceptance_uses_canonical_cases() -> None:
    cases = build_acceptance_cases()

    assert [case.name for case in cases] == sorted(REQUIRED_CASES)
    assert {case.expected_decision for case in cases} == {"allowed"}
    for case in cases:
        assert case.analysis_bundle.human_identity.face_visibility == "fully_visible"
        assert case.analysis_bundle.human_identity.verdict == "allowed"
        assert case.analysis_bundle.garment_identity.garment_count == 1
        assert case.analysis_bundle.material_texture.evidence
        assert case.wear_control_selections
        assert case.wear_control_selections[0].instruction_template


def test_try_on_instruction_expected_decisions() -> None:
    for case_name in REQUIRED_CASES:
        assert expected_decision_for(case_name) == "allowed"
