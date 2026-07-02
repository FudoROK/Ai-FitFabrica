"""Shared admin authentication helpers for internal admin APIs."""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from fastapi.responses import JSONResponse

from src.settings import Settings


@dataclass(frozen=True)
class AdminActor:
    """Resolved backend-owned admin identity."""

    actor_id: str
    role: str


def resolve_admin_actor(
    *,
    settings: Settings,
    allowed_roles: set[str],
    authorization: str | None,
    legacy_admin_role: str | None = None,
    legacy_admin_id: str | None = None,
) -> AdminActor | JSONResponse:
    """Resolve an admin actor from secure bearer token or explicit unsafe staging fallback."""

    token = _bearer_token(authorization)
    configured_token = (getattr(settings, "admin_api_token", None) or "").strip()
    if configured_token:
        if token and hmac.compare_digest(token, configured_token):
            role = sorted(allowed_roles)[0]
            return AdminActor(actor_id="admin-api-token", role=role)
        return _forbidden("admin_auth_invalid", "Valid admin bearer token is required.")

    if bool(getattr(settings, "allow_unsafe_admin_header_auth", False)):
        if legacy_admin_role in allowed_roles and legacy_admin_id:
            return AdminActor(actor_id=legacy_admin_id, role=legacy_admin_role)
        return _forbidden("admin_auth_invalid_legacy_headers", "Valid legacy admin headers are required.")

    return _forbidden(
        "admin_auth_not_configured",
        "Admin API token is not configured and unsafe header auth is disabled.",
    )


def _bearer_token(authorization: str | None) -> str | None:
    """Extract a bearer token from an Authorization header."""

    value = (authorization or "").strip()
    prefix = "Bearer "
    if not value.startswith(prefix):
        return None
    token = value[len(prefix):].strip()
    return token or None


def _forbidden(code: str, message: str) -> JSONResponse:
    """Return one structured admin auth failure."""

    return JSONResponse(status_code=403, content={"error": {"code": code, "message": message}})
