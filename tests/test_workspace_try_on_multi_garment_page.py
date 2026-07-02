"""Guardrails for multi-garment Try-On upload UI."""

from pathlib import Path


def test_try_on_workspace_page_exposes_multi_garment_modes() -> None:
    source = Path("apps/web/src/features/workspace/try-on-workflow.tsx").read_text(encoding="utf-8")
    contracts = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")

    for marker in (
        "single_item",
        "upper_lower",
        "upper_lower_outerwear",
        "full_body",
        "upper_garment_photo",
        "lower_garment_photo",
        "outerwear_garment_photo",
        "full_body_garment_photo",
    ):
        assert marker in source

    assert '"upper_garment_photo"' in contracts
    assert '"lower_garment_photo"' in contracts
    assert '"outerwear_garment_photo"' in contracts
    assert '"full_body_garment_photo"' in contracts
