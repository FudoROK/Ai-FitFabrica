"""Tests for the Try-On sandbox result image asset."""
from __future__ import annotations

from pathlib import Path


def test_try_on_sandbox_result_image_asset_exists() -> None:
    """The sandbox result image path must resolve to a checked-in public asset."""
    asset_path = Path("apps/web/public/images/shared/try-on-sandbox-result.svg")

    assert asset_path.is_file()
