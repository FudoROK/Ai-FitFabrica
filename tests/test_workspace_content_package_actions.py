"""Tests for the workspace content package toolbar actions."""
from __future__ import annotations

from pathlib import Path


def test_workspace_content_package_toolbar_has_real_actions() -> None:
    """The content package toolbar must not ship with three inert buttons."""
    page_source = Path("apps/web/src/app/(workspace)/workspace/content-package/page.tsx").read_text(encoding="utf-8")

    assert 'href="/workspace/history"' in page_source
    assert 'href="/workspace/product-card"' in page_source
    assert "disabled" in page_source
