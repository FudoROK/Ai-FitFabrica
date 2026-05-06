"""CRM identity binding persistence helpers."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict, Optional

from src.domain.constants import LEADS_COLLECTION_NAME
from .firestore_client_factory import require_client_for_write, run_in_transaction, safe_execute

logger = logging.getLogger(__name__)


def upsert_crm_contact_binding(*, lead_id: str, crm_contact_ref: str, crm_provider: str) -> bool:
    if not lead_id or not crm_contact_ref:
        return False
    doc_ref = require_client_for_write().collection(LEADS_COLLECTION_NAME).document(lead_id)
    now = datetime.now(timezone.utc)

    def _transactional_upsert(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        existing_ref = (data.get("crm_contact_ref") or "").strip()
        if existing_ref and existing_ref != str(crm_contact_ref):
            logger.warning(
                "crm_binding_conflict_detected",
                extra={"lead_id": lead_id, "existing_ref": existing_ref, "incoming_ref": crm_contact_ref},
            )
            return False
        payload = {
            "crm_contact_ref": str(crm_contact_ref),
            "crm_provider": str(crm_provider),
            "updated_at": now,
        }
        safe_execute(transaction.set, doc_ref, payload, merge=True)
        return True

    return run_in_transaction(_transactional_upsert)


def upsert_hubspot_contact_id(*, lead_id: str, contact_id: str) -> bool:
    """Backwards-compatible narrow helper for the default HubSpot adapter path."""

    return upsert_crm_contact_binding(
        lead_id=lead_id,
        crm_contact_ref=contact_id,
        crm_provider="hubspot",
    )


def get_crm_identity_binding(*, identity_key: str) -> Optional[Dict[str, Any]]:
    if not identity_key:
        return None
    doc_ref = require_client_for_write().collection("crm_identity_bindings").document(identity_key)
    snapshot = safe_execute(doc_ref.get)
    if not snapshot or not getattr(snapshot, "exists", False):
        return None
    return snapshot.to_dict() or {}


def resolve_or_claim_crm_identity(*, identity_key: str, crm_provider: str) -> Dict[str, Any]:
    if not identity_key:
        return {"status": "invalid"}
    owner_token = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=90)
    doc_ref = require_client_for_write().collection("crm_identity_bindings").document(identity_key)

    def _transactional_claim(transaction: Any) -> Dict[str, Any]:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        existing_ref = (data.get("crm_contact_ref") or "").strip()
        if existing_ref:
            return {"status": "resolved", "crm_contact_ref": existing_ref}
        status = (data.get("status") or "").strip().lower()
        lock_expires_at = data.get("lock_expires_at")
        lock_alive = isinstance(lock_expires_at, datetime) and lock_expires_at > now
        if status == "creating" and lock_alive:
            return {"status": "in_progress"}
        safe_execute(
            transaction.set,
            doc_ref,
            {
                "status": "creating",
                "crm_provider": crm_provider,
                "owner_token": owner_token,
                "lock_expires_at": expires_at,
                "updated_at": now,
            },
            merge=True,
        )
        return {"status": "claimed", "owner_token": owner_token}

    return run_in_transaction(_transactional_claim)


def finalize_crm_identity_binding(
    *,
    identity_key: str,
    owner_token: str,
    crm_contact_ref: str,
    crm_provider: str,
) -> bool:
    if not identity_key or not owner_token or not crm_contact_ref:
        return False
    doc_ref = require_client_for_write().collection("crm_identity_bindings").document(identity_key)
    now = datetime.now(timezone.utc)

    def _transactional_finalize(transaction: Any) -> bool:
        snapshot = safe_execute(doc_ref.get, transaction=transaction)
        data = snapshot.to_dict() or {}
        existing_ref = (data.get("crm_contact_ref") or "").strip()
        if existing_ref and existing_ref != str(crm_contact_ref):
            logger.warning(
                "crm_identity_conflict_on_finalize",
                extra={"identity_key": identity_key, "existing_ref": existing_ref, "incoming_ref": crm_contact_ref},
            )
            return False
        if data.get("owner_token") != owner_token and not existing_ref:
            return False
        safe_execute(
            transaction.set,
            doc_ref,
            {
                "status": "resolved",
                "crm_provider": crm_provider,
                "crm_contact_ref": str(crm_contact_ref),
                "owner_token": None,
                "lock_expires_at": None,
                "updated_at": now,
            },
            merge=True,
        )
        return True

    return run_in_transaction(_transactional_finalize)
