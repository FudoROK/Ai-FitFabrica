"""Guardrails for the web Try-On workspace route contract."""
from __future__ import annotations

from pathlib import Path


WEB_SRC = Path("apps/web/src")
CANONICAL_FITTING_ROUTE = "/workspace/new-fitting"
LEGACY_TRY_ON_ROUTE = "/workspace/try-on/new"


def test_new_fitting_route_is_the_canonical_try_on_entrypoint() -> None:
    """Require public and workspace links to use the project route contract."""
    canonical_page = WEB_SRC / "app" / "(workspace)" / "workspace" / "new-fitting" / "page.tsx"
    legacy_page = WEB_SRC / "app" / "(workspace)" / "workspace" / "try-on" / "new" / "page.tsx"

    assert canonical_page.exists()
    assert legacy_page.exists()

    source_files = [
        path
        for pattern in ("*.ts", "*.tsx")
        for path in WEB_SRC.rglob(pattern)
        if ".next" not in path.parts
        and path != WEB_SRC / "app" / "(workspace)" / "workspace" / "try-on" / "new" / "page.tsx"
    ]
    offenders = [
        str(path)
        for path in source_files
        if LEGACY_TRY_ON_ROUTE in path.read_text(encoding="utf-8")
    ]

    assert offenders == []

    canonical_references = [
        path
        for path in source_files
        if CANONICAL_FITTING_ROUTE in path.read_text(encoding="utf-8")
    ]
    assert canonical_references
