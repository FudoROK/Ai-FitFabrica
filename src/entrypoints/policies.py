from __future__ import annotations

import hmac
import logging
from ipaddress import ip_address
from typing import Optional, Sequence

from fastapi import Request
from google.auth.transport import requests as grequests
from google.oauth2 import id_token


logger = logging.getLogger(__name__)
pubsub_logger = logging.getLogger("pubsub_push")
TRUSTED_GOOGLE_OIDC_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})


def has_valid_token(request: Request, expected_token: Optional[str], header_name: str) -> bool:
    if not expected_token:
        logger.error("Expected auth token is not configured for header %s", header_name)
        return False

    provided_token = request.headers.get(header_name)
    if provided_token is None:
        logger.warning("Missing auth header %s", header_name)
        return False

    return hmac.compare_digest(provided_token, expected_token)


def is_loopback_client(request: Request) -> bool:
    client = request.client
    host = getattr(client, "host", None)
    if not host:
        return False

    normalized_host = str(host).strip().lower()
    if normalized_host == "localhost":
        return True

    try:
        return ip_address(normalized_host).is_loopback
    except ValueError:
        return False


def is_status_endpoint_request_authorized(request: Request, settings) -> bool:
    if is_loopback_client(request):
        return True
    if settings.public_status_endpoints_enabled:
        return True
    return has_valid_token(request, settings.status_endpoint_token, "X-Status-Token")


def verify_pubsub_oidc_jwt(request: Request, settings) -> bool:
    expected_audience = settings.pubsub_push_audience
    expected_email = settings.pubsub_push_service_account_email

    if not expected_audience or not expected_email:
        pubsub_logger.error(
            "Pub/Sub OIDC settings missing; audience=%s email=%s",
            expected_audience,
            expected_email,
        )
        return False

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        pubsub_logger.error("Missing or invalid Authorization bearer header")
        return False

    token = auth[len("Bearer ") :].strip()
    if not token:
        pubsub_logger.error("Missing bearer token in Authorization header")
        return False

    try:
        claims = id_token.verify_oauth2_token(token, grequests.Request(), audience=expected_audience)
    except Exception:
        pubsub_logger.error("Failed to verify Pub/Sub OIDC token for audience %s", expected_audience)
        return False

    issuer = str(claims.get("iss") or "").strip()
    if issuer not in TRUSTED_GOOGLE_OIDC_ISSUERS:
        pubsub_logger.error("Pub/Sub OIDC issuer mismatch; got=%s", issuer)
        return False

    if claims.get("email") != expected_email:
        pubsub_logger.error("Pub/Sub OIDC email mismatch; expected=%s got=%s", expected_email, claims.get("email"))
        return False

    if "email_verified" in claims and claims.get("email_verified") is not True:
        pubsub_logger.error("Pub/Sub OIDC email claim is not verified")
        return False

    return True


def verify_internal_oidc_bearer(
    request: Request,
    *,
    expected_audience: Optional[str],
    allowed_service_accounts: Sequence[str],
    log_name: str,
) -> bool:
    auth_logger = logging.getLogger(log_name)

    normalized_allowed_accounts = {account.strip().lower() for account in allowed_service_accounts if account and account.strip()}
    if not expected_audience or not normalized_allowed_accounts:
        auth_logger.error(
            "Internal OIDC settings missing; audience=%s allowed_accounts_count=%s",
            expected_audience,
            len(normalized_allowed_accounts),
        )
        return False

    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        auth_logger.error("Missing or invalid Authorization bearer header")
        return False

    token = auth[len("Bearer ") :].strip()
    if not token:
        auth_logger.error("Missing bearer token in Authorization header")
        return False

    try:
        claims = id_token.verify_oauth2_token(token, grequests.Request(), audience=expected_audience)
    except Exception:
        auth_logger.error("Failed to verify internal OIDC token for audience %s", expected_audience)
        return False

    issuer = str(claims.get("iss") or "").strip()
    if issuer not in TRUSTED_GOOGLE_OIDC_ISSUERS:
        auth_logger.error("Internal OIDC issuer mismatch; got=%s", issuer)
        return False

    email = str(claims.get("email") or "").strip().lower()
    if not email or email not in normalized_allowed_accounts:
        auth_logger.error("Internal OIDC caller email mismatch; got=%s", claims.get("email"))
        return False

    if "email_verified" in claims and claims.get("email_verified") is not True:
        auth_logger.error("Internal OIDC email claim is not verified")
        return False

    return True


def normalize_idempotency_key_parts(channel: object, event_identity: object) -> tuple[str, str]:
    normalized_channel = str(channel).strip().lower() if channel is not None else ""
    normalized_event_identity = str(event_identity).strip() if event_identity is not None else ""

    if not normalized_channel:
        raise ValueError("Invalid idempotency channel")
    if not normalized_event_identity:
        raise ValueError("Invalid idempotency event_identity")
    if "none" in (normalized_channel.lower(), normalized_event_identity.lower()):
        raise ValueError("Idempotency key must not contain None")

    return normalized_channel, normalized_event_identity
