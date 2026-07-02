"""Daily summary persistence helpers."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from .firestore_client_factory import run_in_transaction, safe_execute
from .summary_store_core import (
    LEAD_MEMORIES_COLLECTION_NAME,
    MEMORY_ROOT_VERSION,
    doc_path,
    ensure_memory_root_document,
    get_firestore_client,
    logger,
    memory_root_ref,
    require_client_for_write,
)
def fetch_daily_summary(
    lead_id: str,
    memory_day_key: str,
    *,
    get_client=get_firestore_client,
    safe_execute_fn=safe_execute,
) -> Optional[Dict[str, Any]]:
    if not lead_id or not memory_day_key:
        return None
    client = get_client()
    if not client:
        logger.warning("Skipping daily summary fetch; Firestore unavailable")
        return None

    doc_ref = client.collection(LEAD_MEMORIES_COLLECTION_NAME).document(lead_id).collection("daily_summaries").document(memory_day_key)
    snapshot = safe_execute_fn(doc_ref.get)
    if snapshot and getattr(snapshot, "exists", False):
        return snapshot.to_dict() or {}
    return None


def fetch_latest_daily_summary(
    lead_id: str,
    *,
    firestore_sdk,
    get_client=get_firestore_client,
    safe_execute_fn=safe_execute,
) -> Optional[Dict[str, Any]]:
    if not lead_id:
        return None
    client = get_client()
    if not client:
        logger.warning("Skipping daily summary fetch; Firestore unavailable")
        return None
    if firestore_sdk is None:  # pragma: no cover
        logger.warning("Skipping daily summary fetch; firestore SDK unavailable")
        return None

    query = (
        client.collection(LEAD_MEMORIES_COLLECTION_NAME)
        .document(lead_id)
        .collection("daily_summaries")
        .order_by("memory_day_key", direction=firestore_sdk.Query.DESCENDING)
        .limit(1)
    )
    docs = safe_execute_fn(query.stream)
    if docs:
        for doc in docs:
            return doc.to_dict() or {}
    return None


def write_daily_summary(
    *,
    lead_id: str,
    memory_day_key: str,
    summary_text: str,
    open_questions: list[str],
    carry_forward_notes: list[str],
    learned_facts: list[str],
    changed_facts: list[str],
    memory_relevance_flags: list[str],
    created_at: datetime,
    messages_used_count: Optional[int] = None,
    source_window_start: Optional[datetime] = None,
    source_window_end: Optional[datetime] = None,
    ensure_root_document=ensure_memory_root_document,
    get_writer=require_client_for_write,
    safe_execute_fn=safe_execute,
) -> bool:
    if not lead_id or not memory_day_key:
        return False
    ensure_root_document(lead_id=lead_id, now=created_at)
    doc_ref = get_writer().collection(LEAD_MEMORIES_COLLECTION_NAME).document(lead_id).collection("daily_summaries").document(memory_day_key)
    payload: Dict[str, Any] = {
        "lead_id": lead_id,
        "memory_day_key": memory_day_key,
        "date": memory_day_key,
        "summary_text": summary_text,
        "open_questions": open_questions,
        "carry_forward_notes": carry_forward_notes,
        "learned_facts": learned_facts,
        "changed_facts": changed_facts,
        "memory_relevance_flags": memory_relevance_flags,
        "created_at": created_at,
        "updated_at": created_at,
    }
    if messages_used_count is not None:
        payload["messages_used_count"] = messages_used_count
    if source_window_start is not None:
        payload["source_window_start"] = source_window_start
    if source_window_end is not None:
        payload["source_window_end"] = source_window_end
    existing = safe_execute_fn(doc_ref.get)
    if existing and getattr(existing, "exists", False):
        existing_payload = existing.to_dict() or {}
        comparable_fields = (
            "summary_text",
            "open_questions",
            "carry_forward_notes",
            "learned_facts",
            "changed_facts",
            "memory_relevance_flags",
        )
        same_payload = all(existing_payload.get(field) == payload.get(field) for field in comparable_fields)
        if same_payload:
            logger.info("memory_daily_summary_write_idempotent_already_applied", extra={"lead_id": lead_id, "memory_day_key": memory_day_key})
            return True
        logger.warning("memory_daily_summary_write_conflict_payload_mismatch", extra={"lead_id": lead_id, "memory_day_key": memory_day_key})
        return False
    logger.info(
        "memory_daily_summary_write_diag_before",
        extra={
            "write_type": "daily_summary_write",
            "diag_confirmation": "this is the daily summary write call",
            "resolved_document_path": doc_path(doc_ref),
            "lead_id": lead_id,
            "memory_day_key": memory_day_key,
            "collection_name": LEAD_MEMORIES_COLLECTION_NAME,
            "subcollection_name": "daily_summaries",
            "payload_top_level_keys": sorted(payload.keys()),
            "path_variant": "new_path",
            "legacy_path_checked_for_write": False,
            "uses_batch_or_transaction": False,
        },
    )
    safe_execute_fn(doc_ref.set, payload)
    logger.info("memory_daily_summary_write_diag_after", extra={"write_type": "daily_summary_write", "resolved_document_path": doc_path(doc_ref), "write_completed_without_exception": True})
    root_ref = memory_root_ref(client=get_writer(), lead_id=lead_id)
    safe_execute_fn(root_ref.set, {"updated_at": created_at, "version": MEMORY_ROOT_VERSION, "lead_id": lead_id}, merge=True)
    logger.info("memory_root_write_diag_after_daily_summary", extra={"write_type": "memory_root_write", "resolved_document_path": doc_path(root_ref), "write_completed_without_exception": True, "triggered_by_daily_summary_write": True})
    return True


def acquire_memory_write_guard(
    *,
    lead_id: str,
    idempotency_key: str,
    created_at: datetime,
    ensure_root_document=ensure_memory_root_document,
    get_writer=require_client_for_write,
    safe_execute_fn=safe_execute,
    run_transaction=run_in_transaction,
) -> bool:
    if not lead_id or not idempotency_key:
        return False
    ensure_root_document(lead_id=lead_id, now=created_at)
    client = get_writer()
    new_guard_ref = client.collection(LEAD_MEMORIES_COLLECTION_NAME).document(lead_id).collection("memory_write_guards").document(idempotency_key)

    def _work(transaction) -> bool:
        existing_new = safe_execute_fn(new_guard_ref.get, transaction=transaction)
        if existing_new and getattr(existing_new, "exists", False):
            return False
        payload: Dict[str, Any] = {
            "idempotency_key": idempotency_key,
            "lead_id": lead_id,
            "created_at": created_at,
            "updated_at": created_at,
        }
        root_ref = memory_root_ref(client=client, lead_id=lead_id)
        logger.info(
            "memory_transaction_refs_diag_before_commit",
            extra={
                "write_type": "memory_write_guard_transaction",
                "uses_batch_or_transaction": True,
                "transaction_daily_summary_doc_ref": None,
                "transaction_rolling_summary_doc_ref": None,
                "transaction_guard_doc_ref": doc_path(new_guard_ref),
                "transaction_memory_root_doc_ref": doc_path(root_ref),
                "daily_summary_ref_present_in_transaction": False,
            },
        )
        safe_execute_fn(transaction.create, new_guard_ref, payload)
        safe_execute_fn(transaction.set, root_ref, {"updated_at": created_at, "version": MEMORY_ROOT_VERSION, "lead_id": lead_id}, merge=True)
        return True

    return bool(run_transaction(_work))


def release_memory_write_guard(
    *,
    lead_id: str,
    idempotency_key: str,
    get_writer=require_client_for_write,
    safe_execute_fn=safe_execute,
) -> None:
    if not lead_id or not idempotency_key:
        return
    guard_ref = get_writer().collection(LEAD_MEMORIES_COLLECTION_NAME).document(lead_id).collection("memory_write_guards").document(idempotency_key)
    safe_execute_fn(guard_ref.delete)


__all__ = [
    "acquire_memory_write_guard",
    "fetch_daily_summary",
    "fetch_latest_daily_summary",
    "release_memory_write_guard",
    "write_daily_summary",
]
