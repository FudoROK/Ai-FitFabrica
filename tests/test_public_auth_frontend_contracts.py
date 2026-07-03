"""Guardrails for public auth frontend contracts."""

from pathlib import Path


def test_frontend_auth_contracts_and_client_methods_exist() -> None:
    contracts_source = Path("apps/web/src/lib/api/contracts.ts").read_text(encoding="utf-8")
    client_source = Path("apps/web/src/lib/api/client.ts").read_text(encoding="utf-8")

    assert "export type AuthSessionResponse" in contracts_source
    assert "authenticated: boolean" in contracts_source
    assert "auth_configured: boolean" in contracts_source
    assert "export type AuthLogoutResponse" in contracts_source
    assert "getAuthSession()" in client_source
    assert "/auth/session" in client_source
    assert "logout()" in client_source
    assert "/auth/logout" in client_source
