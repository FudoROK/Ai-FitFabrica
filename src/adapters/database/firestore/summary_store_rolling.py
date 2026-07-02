"""Rolling summary persistence helpers."""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Dict, Optional

from src.domain.memory.rolling_content_policy import validate as validate_rolling_content

from .firestore_client_factory import run_in_transaction, safe_execute
from .summary_store_core import (
    LEAD_MEMORIES_COLLECTION_NAME,
    MEMORY_ROOT_VERSION,
    ROLLING_ARTIFACTS_COLLECTION_NAME,
    ROLLING_CURRENT_POINTER_COLLECTION_NAME,
    ROLLING_CURRENT_POINTER_DOC_ID,
    doc_path,
    ensure_memory_root_document,
    get_firestore_client,
    lead_memory_doc_ref,
    logger,
    memory_root_ref,
    require_client_for_write,
    rolling_pointer_read_enabled,
)


def fetch_rolling_summary(
    *,
    lead_id: str,
    get_client=get_firestore_client,
    pointer_reads_enabled=rolling_pointer_read_enabled,
    fetch_pointer=None,
    fetch_artifact=None,
) -> Optional[Dict[str, Any]]:
    if not lead_id:
        return None
    client = get_client()
    if not client:
        logger.warning("Skipping rolling summary fetch; Firestore unavailable")
        return None
    if not pointer_reads_enabled():
        return None
    fetch_pointer = fetch_pointer or fetch_current_rolling_pointer
    fetch_artifact = fetch_artifact or fetch_rolling_artifact
    pointer = fetch_pointer(lead_id=lead_id)
    if isinstance(pointer, dict):
        artifact_id = pointer.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id.strip():
            artifact_payload = fetch_artifact(lead_id=lead_id, artifact_id=artifact_id.strip())
            if isinstance(artifact_payload, dict) and is_canonical_rolling_payload(artifact_payload):
                return artifact_payload
    return None


def is_canonical_rolling_payload(payload: Dict[str, Any]) -> bool:
    summary_text = payload.get("rolling_summary_text")
    if not isinstance(summary_text, str):
        return False
    validation = validate_rolling_content(summary_text)
    return bool(validation.ok)


def build_rolling_hash(*, rolling_summary_text: object) -> str | None:
    if not isinstance(rolling_summary_text, str):
        return None
    normalized = rolling_summary_text.strip()
    if not normalized:
        return None
    return sha256(normalized.encode("utf-8")).hexdigest()


def build_rolling_artifact_id(*, lead_id: str, rolling_payload: Dict[str, Any]) -> str | None:
    summary_text = rolling_payload.get("rolling_summary_text")
    if not isinstance(summary_text, str) or not summary_text.strip():
        return None
    rolling_hash = rolling_payload.get("rolling_hash")
    if not isinstance(rolling_hash, str) or not rolling_hash.strip():
        rolling_hash = build_rolling_hash(rolling_summary_text=summary_text)
    version = rolling_payload.get("version")
    version_part = str(version) if version is not None else "na"
    if not rolling_hash:
        return None
    raw = f"{lead_id.strip()}:{version_part}:{rolling_hash.strip()}"
    return sha256(raw.encode("utf-8")).hexdigest()


def fetch_current_rolling_pointer(*, lead_id: str, get_client=get_firestore_client, safe_execute_fn=safe_execute) -> Optional[Dict[str, Any]]:
    if not lead_id:
        return None
    client = get_client()
    if not client:
        return None
    pointer_ref = lead_memory_doc_ref(client=client, lead_id=lead_id).collection(ROLLING_CURRENT_POINTER_COLLECTION_NAME).document(ROLLING_CURRENT_POINTER_DOC_ID)
    snapshot = safe_execute_fn(pointer_ref.get)
    if snapshot and getattr(snapshot, "exists", False):
        return snapshot.to_dict() or {}
    return None


def fetch_rolling_artifact(
    *,
    lead_id: str,
    artifact_id: str,
    get_client=get_firestore_client,
    safe_execute_fn=safe_execute,
) -> Optional[Dict[str, Any]]:
    if not lead_id or not artifact_id:
        return None
    client = get_client()
    if not client:
        return None
    artifact_ref = lead_memory_doc_ref(client=client, lead_id=lead_id).collection(ROLLING_ARTIFACTS_COLLECTION_NAME).document(artifact_id)
    snapshot = safe_execute_fn(artifact_ref.get)
    if snapshot and getattr(snapshot, "exists", False):
        return snapshot.to_dict() or {}
    return None


def create_rolling_artifact(
    *,
    lead_id: str,
    artifact_id: str,
    artifact_payload: Dict[str, Any],
    already_exists_error,
    ensure_root_document=ensure_memory_root_document,
    get_writer=require_client_for_write,
    safe_execute_fn=safe_execute,
) -> bool:
    if not lead_id or not artifact_id:
        return False
    ensure_root_document(lead_id=lead_id, now=artifact_payload.get("updated_at") or datetime.now(tz=timezone.utc))
    client = get_writer()
    artifact_ref = lead_memory_doc_ref(client=client, lead_id=lead_id).collection(ROLLING_ARTIFACTS_COLLECTION_NAME).document(artifact_id)
    existing = safe_execute_fn(artifact_ref.get)
    if existing and getattr(existing, "exists", False):
        return True
    payload = dict(artifact_payload or {})
    payload["artifact_id"] = artifact_id
    payload["lead_id"] = lead_id
    if "rolling_hash" not in payload or not str(payload.get("rolling_hash") or "").strip():
        payload["rolling_hash"] = build_rolling_hash(rolling_summary_text=payload.get("rolling_summary_text"))
    try:
        safe_execute_fn(artifact_ref.create, payload)
    except already_exists_error:
        return True
    return True


def promote_rolling_pointer(
    *,
    lead_id: str,
    artifact_id: str,
    pointer_payload: Dict[str, Any],
    get_writer=require_client_for_write,
    safe_execute_fn=safe_execute,
    run_transaction=run_in_transaction,
) -> bool:
    if not lead_id or not artifact_id:
        return False
    client = get_writer()
    pointer_ref = lead_memory_doc_ref(client=client, lead_id=lead_id).collection(ROLLING_CURRENT_POINTER_COLLECTION_NAME).document(ROLLING_CURRENT_POINTER_DOC_ID)
    artifact_ref = lead_memory_doc_ref(client=client, lead_id=lead_id).collection(ROLLING_ARTIFACTS_COLLECTION_NAME).document(artifact_id)

    def _work(transaction) -> bool:
        artifact_snapshot = safe_execute_fn(artifact_ref.get, transaction=transaction)
        if not artifact_snapshot or not getattr(artifact_snapshot, "exists", False):
            return False
        payload = dict(pointer_payload or {})
        payload["artifact_id"] = artifact_id
        payload["lead_id"] = lead_id
        safe_execute_fn(transaction.set, pointer_ref, payload, merge=True)
        return True

    return bool(run_transaction(_work))


def update_rolling_summary(
    *,
    lead_id: str,
    rolling_update: Dict[str, Any],
    updated_at: datetime,
    extra_fields: Optional[Dict[str, Any]] = None,
    already_exists_error,
    ensure_root_document=ensure_memory_root_document,
    get_writer=require_client_for_write,
    safe_execute_fn=safe_execute,
    create_artifact_fn=create_rolling_artifact,
    promote_pointer_fn=promote_rolling_pointer,
) -> bool:
    if not lead_id:
        return False
    ensure_root_document(lead_id=lead_id, now=updated_at)
    client = get_writer()
    pointer_ref = client.collection(LEAD_MEMORIES_COLLECTION_NAME).document(lead_id).collection(ROLLING_CURRENT_POINTER_COLLECTION_NAME).document(ROLLING_CURRENT_POINTER_DOC_ID)
    payload: Dict[str, Any] = {
        "lead_id": lead_id,
        "rolling_summary_text": rolling_update.get("rolling_summary_text"),
        "open_questions": rolling_update.get("open_questions", []),
        "carry_forward_notes": rolling_update.get("carry_forward_notes", []),
        "days_count": rolling_update.get("days_count"),
        "last_daily_summary_date": rolling_update.get("last_daily_summary_date"),
        "version": rolling_update.get("version"),
        "rolling_hash": rolling_update.get("rolling_hash"),
        "updated_at": updated_at,
    }
    if not isinstance(payload.get("rolling_hash"), str) or not str(payload.get("rolling_hash")).strip():
        payload["rolling_hash"] = build_rolling_hash(rolling_summary_text=payload.get("rolling_summary_text"))
    payload["created_at"] = updated_at
    if isinstance(extra_fields, dict):
        payload.update({key: value for key, value in extra_fields.items() if value is not None})
    artifact_id = build_rolling_artifact_id(lead_id=lead_id, rolling_payload=payload)
    if not artifact_id:
        return False
    artifact_payload = dict(payload)
    artifact_payload["created_at"] = payload.get("created_at") or updated_at
    artifact_created = create_artifact_fn(
        lead_id=lead_id,
        artifact_id=artifact_id,
        artifact_payload=artifact_payload,
        already_exists_error=already_exists_error,
    )
    pointer_promoted = promote_pointer_fn(
        lead_id=lead_id,
        artifact_id=artifact_id,
        pointer_payload={"updated_at": updated_at, "version": payload.get("version"), "rolling_hash": payload.get("rolling_hash")},
    )
    write_materialized = bool(pointer_promoted and artifact_created)
    logger.info("memory_rolling_write_diag_after", extra={"write_type": "rolling_summary_write", "resolved_document_path": doc_path(pointer_ref), "write_completed_without_exception": True, "post_write_materialized": write_materialized})
    if not write_materialized:
        logger.warning("memory_rolling_write_materialization_failed", extra={"write_type": "rolling_summary_write", "resolved_document_path": doc_path(pointer_ref), "materialized": False})
        return False
    root_ref = memory_root_ref(client=get_writer(), lead_id=lead_id)
    safe_execute_fn(root_ref.set, {"updated_at": updated_at, "version": MEMORY_ROOT_VERSION, "lead_id": lead_id}, merge=True)
    logger.info("memory_root_write_diag_after_rolling_summary", extra={"write_type": "memory_root_write", "resolved_document_path": doc_path(root_ref), "write_completed_without_exception": True, "triggered_by_rolling_summary_write": True})
    return True


__all__ = [
    "build_rolling_artifact_id",
    "build_rolling_hash",
    "create_rolling_artifact",
    "fetch_current_rolling_pointer",
    "fetch_rolling_artifact",
    "fetch_rolling_summary",
    "is_canonical_rolling_payload",
    "promote_rolling_pointer",
    "update_rolling_summary",
]
