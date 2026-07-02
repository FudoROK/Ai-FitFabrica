"""Firestore storage compatibility facade and generic document primitives."""
from __future__ import annotations

from typing import Any

try:  # pragma: no cover - optional dependency at runtime
    from google.api_core.exceptions import AlreadyExists
except ImportError:  # pragma: no cover - fallback for local dev
    class AlreadyExists(Exception):
        """Fallback exception when google.api_core is unavailable."""

        pass

from .crm_binding_store import (
    finalize_crm_identity_binding,
    get_crm_identity_binding,
    resolve_or_claim_crm_identity,
    upsert_crm_contact_binding,
    upsert_hubspot_contact_id,
)
from .firestore_client_factory import (
    get_firestore_client,
    require_client_for_write,
    run_in_transaction,
    run_in_transaction_with_client,
    safe_execute,
)
from .lead_store import (
    _lead_from_doc,
    _session_from_doc,
    apply_lead_patch,
    apply_lead_profile_patch,
    create_or_get_canonical_lead,
    get_lead_by_id,
    get_or_create_chat_session,
    lead_doc_ref,
    update_chat_session,
    update_lead,
    update_lead_activity,
    write_extraction_attempt,
)
from .message_store import append_message_with_ttl, fetch_messages_in_window, fetch_recent_messages

def get_document(collection: str, doc_id: str) -> Optional[dict[str, Any]]:
    client = get_firestore_client()
    if not client:
        return None
    snapshot = safe_execute(client.collection(collection).document(doc_id).get)
    if snapshot and getattr(snapshot, "exists", False):
        return snapshot.to_dict() or {}
    return None


def patch_document(collection: str, doc_id: str, payload: dict[str, Any]) -> None:
    """Apply a partial document patch using merge semantics.

    Canonical Firestore write contract:
    - patch/update flows MUST use merge writes so concurrent writers do not wipe each other's fields;
    - full replacement is allowed only via `explicit_replace_document`.
    """

    doc_ref = require_client_for_write().collection(collection).document(doc_id)
    safe_execute(doc_ref.set, payload, merge=True)


def explicit_replace_document(collection: str, doc_id: str, payload: dict[str, Any]) -> None:
    """Replace a whole document intentionally (restricted, explicit path only)."""

    doc_ref = require_client_for_write().collection(collection).document(doc_id)
    safe_execute(doc_ref.set, payload, merge=False)


def create_document(collection: str, doc_id: str, payload: dict[str, Any]) -> bool:
    doc_ref = require_client_for_write().collection(collection).document(doc_id)
    try:
        safe_execute(doc_ref.create, payload)
        return True
    except AlreadyExists:
        return False
