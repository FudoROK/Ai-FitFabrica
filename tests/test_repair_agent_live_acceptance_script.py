from __future__ import annotations

from pathlib import Path

import pytest

from scripts.repair_agent_live_acceptance import REQUIRED_CASES, collect_acceptance_cases, expected_scope_for


def test_repair_agent_acceptance_requires_quality_verifier_dataset(tmp_path: Path) -> None:
    missing_case = REQUIRED_CASES[0]

    with pytest.raises(ValueError, match=missing_case):
        collect_acceptance_cases(tmp_path)


def test_repair_agent_acceptance_collects_required_cases(tmp_path: Path) -> None:
    for case_name in REQUIRED_CASES:
        case_dir = tmp_path / case_name
        case_dir.mkdir()
        (case_dir / "generated_result.png").write_bytes(b"image")

    cases = collect_acceptance_cases(tmp_path)

    assert [case.name for case in cases] == sorted(REQUIRED_CASES)
    assert {case.expected_scope for case in cases} == {"local", "unsafe"}


@pytest.mark.parametrize(
    ("case_name", "expected"),
    [
        ("minor_background_artifact", "local"),
        ("minor_color_shift", "local"),
        ("face_changed", "unsafe"),
        ("severe_anatomy_artifact", "unsafe"),
    ],
)
def test_repair_agent_expected_scopes(case_name: str, expected: str) -> None:
    assert expected_scope_for(case_name) == expected
