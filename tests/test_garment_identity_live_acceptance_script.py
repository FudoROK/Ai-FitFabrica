from __future__ import annotations

from pathlib import Path

import pytest

from scripts.garment_identity_live_acceptance import REQUIRED_CASES, collect_acceptance_assets, expected_decision_for


def test_collect_acceptance_assets_requires_exact_named_dataset(tmp_path: Path) -> None:
    for file_name in REQUIRED_CASES:
        (tmp_path / file_name).write_bytes(b"image")

    assets = collect_acceptance_assets(tmp_path)

    assert [asset.path.name for asset in assets] == sorted(REQUIRED_CASES)


def test_collect_acceptance_assets_reports_missing_files(tmp_path: Path) -> None:
    (tmp_path / "good_single_shirt.png").write_bytes(b"image")

    with pytest.raises(ValueError) as exc_info:
        collect_acceptance_assets(tmp_path)

    assert "missing required garment acceptance files" in str(exc_info.value)
    assert "not_garment.png" in str(exc_info.value)


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("good_single_shirt.png", "allowed"),
        ("coat_or_jacket.png", "allowed"),
        ("dress.png", "allowed"),
        ("pants_or_jeans.png", "allowed"),
        ("patterned_item.png", "allowed"),
        ("logo_or_print_item.png", "allowed"),
        ("dark_or_blurry_garment.png", "blocked"),
        ("cropped_garment.png", "blocked"),
        ("multiple_garments.png", "blocked"),
        ("not_garment.png", "blocked"),
    ],
)
def test_expected_decision_for_acceptance_cases(file_name: str, expected: str) -> None:
    assert expected_decision_for(file_name) == expected
