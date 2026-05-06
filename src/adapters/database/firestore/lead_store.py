"""Lead and chat persistence helpers."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.domain.constants import LEADS_COLLECTION_NAME
from src.domain.models import ChatSession, Lead
from .firestore_client_factory import get_firestore_client, require_client_for_write, safe_execute

logger = logging.getLogger(__name__)

_ALLOWED_LEAD_FIELDS = set(Lead.model_fields)
_ALLOWED_SESSION_FIELDS = set(ChatSession.model_fields)


def lead_doc_ref(lead_id: str):
    client = require_client_for_write()
    return client.collection(LEADS_COLLECTION_NAME).document(str(lead_id))


def _session_from_doc(doc: Any) -> ChatSession:
    data = doc.to_dict() if doc else None
    if not data:
        return ChatSession()

    filtered: Dict[str, Any] = {k: v for k, v in data.items() if k in _ALLOWED_SESSION_FIELDS}

    if "chat_id" in filtered and filtered["chat_id"] is not None and not isinstance(filtered["chat_id"], str):
        filtered["chat_id"] = str(filtered["chat_id"])

    if (
        "external_user_id" in filtered
        and filtered["external_user_id"] is not None
        and not isinstance(filtered["external_user_id"], str)
    ):
        filtered["external_user_id"] = str(filtered["external_user_id"])

    try:
        return ChatSession(**filtered)
    except Exception:  # pragma: no cover
        logger.exception("Failed to hydrate ChatSession from Firestore, returning empty session")
        return ChatSession()


def _lead_from_doc(doc: Any) -> Lead:
    data = doc.to_dict() if doc else None
    if not data:
        return Lead()
    filtered_data = {k: v for k, v in data.items() if k in _ALLOWED_LEAD_FIELDS}
    filtered_data["username_or_contact"] = data.get("username_or_contact")
    filtered_data["contact_channel"] = data.get("contact_channel")
    filtered_data["contact_details"] = data.get("contact_details")
    filtered_data["has_contact"] = data.get("has_contact", False)
    filtered_data["crm_contact_ref"] = data.get("crm_contact_ref")
    filtered_data["crm_provider"] = data.get("crm_provider")
    filtered_data["lead_profile"] = data.get("lead_profile") if isinstance(data.get("lead_profile"), dict) else {}
    return Lead(**filtered_data)


def get_or_create_chat_session(channel: str, external_user_id: str, username: Optional[str] = None) -> Optional[ChatSession]:
    client = get_firestore_client()
    if not client:
        logger.warning("Firestore unavailable, returning empty chat session")
        return None

    doc_id = f"{channel}:{external_user_id}"
    doc_ref = client.collection("chats").document(doc_id)
    snapshot = safe_execute(doc_ref.get)
    if snapshot and snapshot.exists:
        session = _session_from_doc(snapshot)
        session.id = doc_id
        return session

    now = datetime.now(timezone.utc)
    session = ChatSession(
        id=doc_id,
        channel=channel,
        chat_id=external_user_id,
        external_user_id=external_user_id,
        last_messages=[],
        created_at=now,
        updated_at=now,
    )
    safe_execute(doc_ref.set, session.model_dump(exclude_none=True))
    return session


def update_chat_session(session: ChatSession) -> None:
    client = get_firestore_client()
    if not client or not session or not session.id:
        logger.warning("Skipping chat session update; Firestore unavailable or session missing")
        return
    safe_execute(client.collection("chats").document(session.id).set, session.model_dump(exclude_none=True), merge=True)


def get_lead_by_id(lead_id: Optional[str]) -> Optional[Lead]:
    if not lead_id:
        return None
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping lead fetch; Firestore unavailable")
        return None

    snapshot = safe_execute(client.collection(LEADS_COLLECTION_NAME).document(lead_id).get)
    if snapshot and snapshot.exists:
        lead = _lead_from_doc(snapshot)
        lead.lead_id = lead.lead_id or lead_id
        return lead
    return None


def create_or_get_canonical_lead(
    *,
    canonical_lead_id: str,
    channel: str,
    external_user_id: str,
    username: Optional[str],
    first_name: Optional[str],
) -> Optional[Lead]:
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping canonical lead creation; Firestore unavailable")
        return None

    doc_ref = client.collection(LEADS_COLLECTION_NAME).document(str(canonical_lead_id))
    existing = safe_execute(doc_ref.get)
    if existing and getattr(existing, "exists", False):
        lead = _lead_from_doc(existing)
        lead.lead_id = lead.lead_id or canonical_lead_id
        updated = False
        if first_name and not lead.first_name:
            lead.first_name = first_name
            lead.has_name = True
            updated = True
        if username and not lead.username_or_contact:
            lead.username_or_contact = username
            updated = True
        if updated:
            update_lead(lead)
        return lead

    now = datetime.now(timezone.utc)
    lead = Lead(
        lead_id=str(canonical_lead_id),
        primary_channel=channel,
        channel_user_id=external_user_id,
        username_or_contact=username,
        first_name=first_name,
        has_contact=False,
        has_name=bool(first_name),
        has_business=False,
        timestamp_created=now,
        last_contact_at=now,
    )
    safe_execute(doc_ref.set, lead.model_dump(exclude_none=True))
    return lead


def update_lead(lead: Optional[Lead]) -> None:
    if not lead or not lead.lead_id:
        return
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping lead update; Firestore unavailable")
        return

    data = lead.model_dump(exclude_none=True)
    data["username_or_contact"] = lead.username_or_contact
    data["contact_channel"] = lead.contact_channel
    data["contact_details"] = lead.contact_details
    data["has_contact"] = lead.has_contact
    safe_execute(client.collection(LEADS_COLLECTION_NAME).document(lead.lead_id).set, data, merge=True)


def apply_lead_profile_patch(lead_id: Optional[str], profile: Dict[str, Any]) -> bool:
    if not lead_id:
        return False
    return apply_lead_patch(str(lead_id), {"lead_profile": profile or {}})


def apply_lead_patch(lead_id: Optional[str], lead_patch: Dict[str, Any]) -> bool:
    if not lead_id:
        return False

    payload = dict(lead_patch or {})
    nullable_fields = {"timezone"}
    payload = {
        key: value
        for key, value in payload.items()
        if (value is not None or key in nullable_fields) and not (isinstance(value, str) and not value.strip())
    }
    if not payload:
        return False

    now = datetime.now(timezone.utc)
    payload.setdefault("last_contact_at", now)
    payload.setdefault("last_activity_at", now)
    payload["updated_at"] = now
    payload["updated_at_iso"] = now.isoformat()

    safe_execute(lead_doc_ref(str(lead_id)).set, payload, merge=True)
    return True


def write_extraction_attempt(lead_id: Optional[str], attempt: Dict[str, Any]) -> bool:
    if not lead_id:
        return False
    client = require_client_for_write()
    now = datetime.now(timezone.utc)
    payload = {
        "task_name": attempt.get("task_name"),
        "schema_version": attempt.get("schema_version") or "v1",
        "provider": attempt.get("provider"),
        "status": attempt.get("status"),
        "attempt": attempt.get("attempt"),
        "error_type": attempt.get("error_type"),
        "confidence": float(attempt.get("confidence") or 0.0),
        "missing_count": int(attempt.get("missing_count") or 0),
        "patch_size": int(attempt.get("patch_size") or 0),
        "created_at": now,
    }
    raw_response = attempt.get("raw_response")
    if payload.get("status") != "success" and isinstance(raw_response, str) and raw_response:
        payload["raw_response"] = raw_response[:20000]
    doc_ref = client.collection(LEADS_COLLECTION_NAME).document(str(lead_id)).collection("extraction_attempts").document()
    safe_execute(doc_ref.set, payload)
    return True


def update_lead_activity(lead_id: Optional[str], activity_at: datetime) -> bool:
    if not lead_id:
        return False
    doc_ref = require_client_for_write().collection(LEADS_COLLECTION_NAME).document(str(lead_id))
    safe_execute(doc_ref.set, {"last_activity_at": activity_at, "last_activity_at_iso": activity_at.isoformat()}, merge=True)
    return True
