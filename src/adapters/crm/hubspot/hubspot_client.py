"""HubSpot CRM API client helpers (canonical CRM namespace)."""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from ....settings import load_settings
from ....utils.log_redaction import redact

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

_missing_token_logged = False


def _get_token() -> Optional[str]:
    global _missing_token_logged
    token = load_settings().hubspot.access_token
    if not token and not _missing_token_logged:
        logger.warning("HUBSPOT token is not set; HubSpot integration is disabled")
        _missing_token_logged = True
    return token


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _log_response_error(action: str, response: httpx.Response) -> None:
    content_type = response.headers.get("content-type", "")
    body_preview = response.text if "application/json" in content_type.lower() else response.reason_phrase
    error_summary = redact(body_preview)[:200] if body_preview else "hubspot_error"
    logger.error(
        "hubspot_request_failed",
        extra={
            "task": "hubspot_request",
            "status": "failed",
            "provider": "hubspot",
            "action": action,
            "status_code": response.status_code,
            "error_type": "http_status_error",
            "error_summary": error_summary,
        },
    )


def _request(method: str, path: str, payload: Optional[dict] = None) -> Optional[httpx.Response]:
    token = _get_token()
    if not token:
        return None
    url = f"{load_settings().hubspot.base_url}{path}"
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as request_client:
            response = request_client.request(method, url, json=payload, headers=_headers(token))
    except httpx.RequestError as exc:
        logger.error(
            "hubspot_request_error",
            extra={
                "task": "hubspot_request",
                "status": "failed",
                "provider": "hubspot",
                "action": f"{method} {path}",
                "error_type": type(exc).__name__,
                "error_summary": redact(exc)[:200],
            },
        )
        return None
    if response.is_error:
        _log_response_error(f"{method} {path}", response)
        return None
    return response


def search_contact_by_telegram_id(tg_id: str) -> Optional[str]:
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "telegram_user_id",
                        "operator": "EQ",
                        "value": tg_id,
                    }
                ]
            }
        ],
        "limit": 1,
    }
    response = _request("POST", "/crm/v3/objects/contacts/search", payload)
    if not response:
        return None
    data = response.json()
    results = data.get("results", [])
    if not results:
        return None
    return results[0].get("id")


def create_contact(tg_id: str, firstname: Optional[str] = None) -> Optional[str]:
    properties = {"telegram_user_id": tg_id}
    if firstname:
        properties["firstname"] = firstname
    payload = {"properties": properties}
    response = _request("POST", "/crm/v3/objects/contacts", payload)
    if not response:
        return None
    data = response.json()
    return data.get("id")


def get_contact(contact_id: str, properties: list[str]) -> Optional[dict]:
    props_param = ",".join(properties)
    response = _request("GET", f"/crm/v3/objects/contacts/{contact_id}?properties={props_param}")
    if not response:
        return None
    return response.json()


def update_contact(contact_id: str, properties: dict) -> None:
    if not properties:
        return
    payload = {"properties": properties}
    response = _request("PATCH", f"/crm/v3/objects/contacts/{contact_id}", payload)
    if response is None:
        raise RuntimeError(f"HubSpot contact update failed for contact_id={contact_id}")
    return None


def hubspot_enabled() -> bool:
    return bool(_get_token())


__all__ = [
    "search_contact_by_telegram_id",
    "create_contact",
    "get_contact",
    "update_contact",
    "hubspot_enabled",
]
