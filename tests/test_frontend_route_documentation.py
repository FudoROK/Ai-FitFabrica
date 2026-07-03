"""Guardrails keeping documented web routes aligned with the Next app tree."""

from pathlib import Path


APP_ROOT = Path("apps/web/src/app")


def test_readme_lists_active_frontend_routes() -> None:
    """Every active page route should be visible in README for acceptance sweeps."""

    readme = Path("README.md").read_text(encoding="utf-8")
    for route in _active_page_routes():
        assert f"- `{route}`" in readme, f"README.md does not list active frontend route {route}"


def _active_page_routes() -> list[str]:
    routes: list[str] = []
    for page in APP_ROOT.rglob("page.tsx"):
        parts = page.relative_to(APP_ROOT).parts[:-1]
        visible_parts = [part for part in parts if not (part.startswith("(") and part.endswith(")"))]
        route = "/" + "/".join(visible_parts)
        routes.append(route.rstrip("/") or "/")
    return sorted(routes)
