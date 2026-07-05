"""Guardrails for public frontend routes and auth UI."""

from pathlib import Path


def test_required_public_route_aliases_exist() -> None:
    assert Path("apps/web/src/app/(public)/login/page.tsx").exists()
    assert Path("apps/web/src/app/(public)/contact/page.tsx").exists()
    assert Path("apps/web/src/app/(public)/features/page.tsx").exists()
    assert Path("apps/web/src/app/(public)/about/page.tsx").exists()


def test_required_public_routes_are_visible_in_navigation() -> None:
    source = Path("apps/web/src/lib/routes/public-routes.ts").read_text(encoding="utf-8")

    assert 'href: "/features"' in source
    assert 'href: "/about"' in source


def test_sign_in_form_has_no_decorative_auth_buttons() -> None:
    source = Path("apps/web/src/features/public/sign-in-form.tsx").read_text(encoding="utf-8")

    assert "Продолжить с Google" not in source
    assert "Забыли пароль?" not in source
    assert "client.signIn" in source


def test_sign_in_form_checks_auth_session_contract() -> None:
    source = Path("apps/web/src/features/public/sign-in-form.tsx").read_text(encoding="utf-8")

    assert "client.getAuthSession" in source
    assert "auth_configured" in source
    assert "auth не подключен" in source
