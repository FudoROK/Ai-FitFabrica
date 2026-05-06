"""Message persistence helpers."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from .firestore_client_factory import firestore, get_firestore_client, require_client_for_write, safe_execute

logger = logging.getLogger(__name__)


def _append_message_with_ttl_and_return_id(
    *,
    lead_id: str,
    role: str,
    text: str,
    timestamp: datetime,
    channel: Optional[str] = None,
    chat_id: Optional[str] = None,
    external_user_id: Optional[str] = None,
    ttl_days: int = 180,
    message_idempotency_key: Optional[str] = None,
) -> str | None:
    if not lead_id:
        return None
    client = require_client_for_write()
    expires_at = timestamp + timedelta(days=ttl_days)
    payload: Dict[str, Any] = {
        "lead_id": lead_id,
        "role": role,
        "text": text,
        "timestamp": timestamp,
        "created_at": timestamp,
        "expires_at": expires_at,
        "channel": channel,
        "chat_id": str(chat_id) if chat_id is not None else None,
        "external_user_id": str(external_user_id) if external_user_id is not None else None,
    }
    doc_ref = (
        client.collection("messages").document(str(message_idempotency_key))
        if message_idempotency_key
        else client.collection("messages").document()
    )
    safe_execute(doc_ref.set, {k: v for k, v in payload.items() if v is not None}, merge=bool(message_idempotency_key))
    doc_id = getattr(doc_ref, "id", None) or getattr(doc_ref, "doc_id", None) or message_idempotency_key
    return str(doc_id) if doc_id is not None else None


def append_message_with_ttl(
    *,
    lead_id: str,
    role: str,
    text: str,
    timestamp: datetime,
    channel: Optional[str] = None,
    chat_id: Optional[str] = None,
    external_user_id: Optional[str] = None,
    ttl_days: int = 180,
    message_idempotency_key: Optional[str] = None,
) -> bool:
    message_id = _append_message_with_ttl_and_return_id(
        lead_id=lead_id,
        role=role,
        text=text,
        timestamp=timestamp,
        channel=channel,
        chat_id=chat_id,
        external_user_id=external_user_id,
        ttl_days=ttl_days,
        message_idempotency_key=message_idempotency_key,
    )
    return bool(message_id)


def fetch_recent_messages(lead_id: str, *, since: datetime, limit: int = 30) -> list[Dict[str, Any]]:
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping messages fetch; Firestore unavailable")
        return []
    if firestore is None:  # pragma: no cover
        logger.warning("Skipping messages fetch; firestore SDK unavailable")
        return []
    query = (
        client.collection("messages")
        .where(filter=firestore.FieldFilter("lead_id", "==", lead_id))
        .where(filter=firestore.FieldFilter("timestamp", ">=", since))
        .order_by("timestamp", direction=firestore.Query.ASCENDING)
        .limit(limit)
    )
    docs = safe_execute(query.stream)
    return [
        {
            **(doc.to_dict() or {}),
            "message_id": getattr(doc, "id", None),
        }
        for doc in docs
    ] if docs else []


def fetch_messages_in_window(*, lead_id: str, start_utc: datetime, end_utc: datetime, limit: int = 200) -> list[Dict[str, Any]]:
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping messages fetch; Firestore unavailable")
        return []
    if firestore is None:  # pragma: no cover
        logger.warning("Skipping messages fetch; firestore SDK unavailable")
        return []
    query = (
        client.collection("messages")
        .where(filter=firestore.FieldFilter("lead_id", "==", lead_id))
        .where(filter=firestore.FieldFilter("timestamp", ">=", start_utc))
        .where(filter=firestore.FieldFilter("timestamp", "<", end_utc))
        .order_by("timestamp", direction=firestore.Query.ASCENDING)
        .limit(limit)
    )
    docs = safe_execute(query.stream)
    return [
        {
            **(doc.to_dict() or {}),
            "message_id": getattr(doc, "id", None),
        }
        for doc in docs
    ] if docs else []
