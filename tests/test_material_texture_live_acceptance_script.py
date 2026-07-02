from __future__ import annotations

from pathlib import Path

import pytest

from scripts.material_texture_live_acceptance import REQUIRED_CASES, collect_acceptance_assets, expected_decision_for


def test_material_texture_acceptance_requires_canonical_dataset(tmp_path: Path) -> None:
    missing_file = REQUIRED_CASES[0]

    with pytest.raises(ValueError, match=missing_file):
        collect_acceptance_assets(tmp_path)


def test_material_texture_acceptance_collects_all_required_assets(tmp_path: Path) -> None:
    for file_name in REQUIRED_CASES:
        (tmp_path / file_name).write_bytes(b"image")

    assets = collect_acceptance_assets(tmp_path)

    assert [asset.path.name for asset in assets] == sorted(REQUIRED_CASES)
    assert {asset.expected_decision for asset in assets} == {"allowed", "blocked"}


@pytest.mark.parametrize(
    ("file_name", "expected"),
    [
        ("matte_cotton_like.png", "allowed"),
        ("shiny_satin_like.png", "allowed"),
        ("denim_texture.png", "allowed"),
        ("knit_texture.png", "allowed"),
        ("leather_like_finish.png", "allowed"),
        ("sheer_transparent_fabric.png", "allowed"),
        ("dark_or_blurry_fabric.png", "blocked"),
        ("no_material_evidence.png", "blocked"),
    ],
)
def test_material_texture_expected_decisions(file_name: str, expected: str) -> None:
    assert expected_decision_for(file_name) == expected
