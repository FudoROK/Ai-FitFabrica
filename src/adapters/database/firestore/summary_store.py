"""Lead summary persistence helpers."""
from __future__ import annotations

import logging
from hashlib import sha256
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.domain.memory.rolling_content_policy import validate as validate_rolling_content
from src.settings import load_settings

try:  # pragma: no cover - optional dependency at runtime
    from google.api_core.exceptions import AlreadyExists
except ImportError:  # pragma: no cover - fallback for local dev
    class AlreadyExists(Exception):
        """Fallback exception when google.api_core is unavailable."""

        pass

from .firestore_client_factory import (
    firestore,
    get_firestore_client,
    require_client_for_write,
    run_in_transaction,
    safe_execute,
)

logger = logging.getLogger(__name__)

_LEAD_MEMORIES_COLLECTION_NAME = "lead_memories"
_MEMORY_ROOT_VERSION = 1
_ROLLING_ARTIFACTS_COLLECTION_NAME = "rolling_artifacts"
_ROLLING_CURRENT_POINTER_COLLECTION_NAME = "rolling_current"
_ROLLING_CURRENT_POINTER_DOC_ID = "current"


def _memory_root_ref(*, client, lead_id: str):
    return client.collection(_LEAD_MEMORIES_COLLECTION_NAME).document(lead_id)


def _lead_memory_doc_ref(*, client, lead_id: str):
    return client.collection(_LEAD_MEMORIES_COLLECTION_NAME).document(lead_id)


def _doc_path(doc_ref: Any) -> str:
    path = getattr(doc_ref, "path", None)
    if isinstance(path, str) and path:
        return path
    return str(doc_ref)


def _rolling_settings():
    try:
        return load_settings()
    except Exception:  # pragma: no cover - defensive fallback for isolated tests
        return None


def _rolling_pointer_read_enabled() -> bool:
    settings = _rolling_settings()
    if settings is None:
        return True
    return bool(getattr(settings, "memory_rolling_pointer_read_enabled", True))


def _ensure_memory_root_document(*, lead_id: str, now: datetime) -> None:
    client = require_client_for_write()
    root_ref = _memory_root_ref(client=client, lead_id=lead_id)
    existing = safe_execute(root_ref.get)
    if existing and getattr(existing, "exists", False):
        safe_execute(root_ref.set, {"lead_id": lead_id, "updated_at": now, "version": _MEMORY_ROOT_VERSION}, merge=True)
        return
    safe_execute(
        root_ref.set,
        {
            "lead_id": lead_id,
            "created_at": now,
            "updated_at": now,
            "version": _MEMORY_ROOT_VERSION,
        },
        merge=True,
    )


def fetch_daily_summary(lead_id: str, memory_day_key: str) -> Optional[Dict[str, Any]]:
    if not lead_id or not memory_day_key:
        return None
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping daily summary fetch; Firestore unavailable")
        return None

    doc_ref = (
        client.collection(_LEAD_MEMORIES_COLLECTION_NAME)
        .document(lead_id)
        .collection("daily_summaries")
        .document(memory_day_key)
    )
    snapshot = safe_execute(doc_ref.get)
    if snapshot and getattr(snapshot, "exists", False):
        return snapshot.to_dict() or {}
    return None


def fetch_latest_daily_summary(lead_id: str) -> Optional[Dict[str, Any]]:
    if not lead_id:
        return None
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping daily summary fetch; Firestore unavailable")
        return None
    if firestore is None:  # pragma: no cover
        logger.warning("Skipping daily summary fetch; firestore SDK unavailable")
        return None

    query = (
        client.collection(_LEAD_MEMORIES_COLLECTION_NAME)
        .document(lead_id)
        .collection("daily_summaries")
        .order_by("memory_day_key", direction=firestore.Query.DESCENDING)
        .limit(1)
    )
    docs = safe_execute(query.stream)
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
) -> bool:
    if not lead_id or not memory_day_key:
        return False
    _ensure_memory_root_document(lead_id=lead_id, now=created_at)
    doc_ref = (
        require_client_for_write()
        .collection(_LEAD_MEMORIES_COLLECTION_NAME)
        .document(lead_id)
        .collection("daily_summaries")
        .document(memory_day_key)
    )
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
    existing = safe_execute(doc_ref.get)
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
            logger.info(
                "memory_daily_summary_write_idempotent_already_applied",
                extra={
                    "lead_id": lead_id,
                    "memory_day_key": memory_day_key,
                },
            )
            return True
        logger.warning(
            "memory_daily_summary_write_conflict_payload_mismatch",
            extra={
                "lead_id": lead_id,
                "memory_day_key": memory_day_key,
            },
        )
        return False
    logger.info(
        "memory_daily_summary_write_diag_before",
        extra={
            "write_type": "daily_summary_write",
            "diag_confirmation": "this is the daily summary write call",
            "resolved_document_path": _doc_path(doc_ref),
            "lead_id": lead_id,
            "memory_day_key": memory_day_key,
            "collection_name": _LEAD_MEMORIES_COLLECTION_NAME,
            "subcollection_name": "daily_summaries",
            "payload_top_level_keys": sorted(payload.keys()),
            "path_variant": "new_path",
            "legacy_path_checked_for_write": False,
            "uses_batch_or_transaction": False,
        },
    )
    safe_execute(doc_ref.set, payload)
    logger.info(
        "memory_daily_summary_write_diag_after",
        extra={
            "write_type": "daily_summary_write",
            "resolved_document_path": _doc_path(doc_ref),
            "write_completed_without_exception": True,
        },
    )
    root_ref = _memory_root_ref(client=require_client_for_write(), lead_id=lead_id)
    safe_execute(
        root_ref.set,
        {"updated_at": created_at, "version": _MEMORY_ROOT_VERSION, "lead_id": lead_id},
        merge=True,
    )
    logger.info(
        "memory_root_write_diag_after_daily_summary",
        extra={
            "write_type": "memory_root_write",
            "resolved_document_path": _doc_path(root_ref),
            "write_completed_without_exception": True,
            "triggered_by_daily_summary_write": True,
        },
    )
    return True


def acquire_memory_write_guard(*, lead_id: str, idempotency_key: str, created_at: datetime) -> bool:
    if not lead_id or not idempotency_key:
        return False
    _ensure_memory_root_document(lead_id=lead_id, now=created_at)
    client = require_client_for_write()
    new_guard_ref = (
        client.collection(_LEAD_MEMORIES_COLLECTION_NAME)
        .document(lead_id)
        .collection("memory_write_guards")
        .document(idempotency_key)
    )
    def _work(transaction) -> bool:
        existing_new = safe_execute(new_guard_ref.get, transaction=transaction)
        if existing_new and getattr(existing_new, "exists", False):
            return False
        payload: Dict[str, Any] = {
            "idempotency_key": idempotency_key,
            "lead_id": lead_id,
            "created_at": created_at,
            "updated_at": created_at,
        }
        root_ref = _memory_root_ref(client=client, lead_id=lead_id)
        logger.info(
            "memory_transaction_refs_diag_before_commit",
            extra={
                "write_type": "memory_write_guard_transaction",
                "uses_batch_or_transaction": True,
                "transaction_daily_summary_doc_ref": None,
                "transaction_rolling_summary_doc_ref": None,
                "transaction_guard_doc_ref": _doc_path(new_guard_ref),
                "transaction_memory_root_doc_ref": _doc_path(root_ref),
                "daily_summary_ref_present_in_transaction": False,
            },
        )
        safe_execute(transaction.create, new_guard_ref, payload)
        safe_execute(
            transaction.set,
            root_ref,
            {"updated_at": created_at, "version": _MEMORY_ROOT_VERSION, "lead_id": lead_id},
            merge=True,
        )
        return True

    return bool(run_in_transaction(_work))


def release_memory_write_guard(*, lead_id: str, idempotency_key: str) -> None:
    if not lead_id or not idempotency_key:
        return
    guard_ref = (
        require_client_for_write()
        .collection(_LEAD_MEMORIES_COLLECTION_NAME)
        .document(lead_id)
        .collection("memory_write_guards")
        .document(idempotency_key)
    )
    safe_execute(guard_ref.delete)


def fetch_rolling_summary(*, lead_id: str) -> Optional[Dict[str, Any]]:
    if not lead_id:
        return None
    client = get_firestore_client()
    if not client:
        logger.warning("Skipping rolling summary fetch; Firestore unavailable")
        return None

    if not _rolling_pointer_read_enabled():
        return None
    pointer = fetch_current_rolling_pointer(lead_id=lead_id)
    if isinstance(pointer, dict):
        artifact_id = pointer.get("artifact_id")
        if isinstance(artifact_id, str) and artifact_id.strip():
            artifact_payload = fetch_rolling_artifact(lead_id=lead_id, artifact_id=artifact_id.strip())
            if isinstance(artifact_payload, dict) and _is_canonical_rolling_payload(artifact_payload):
                return artifact_payload
    return None


def _is_canonical_rolling_payload(payload: Dict[str, Any]) -> bool:
    summary_text = payload.get("rolling_summary_text")
    if not isinstance(summary_text, str):
        return False
    validation = validate_rolling_content(summary_text)
    if not validation.ok:
        return False
    return True


def _build_rolling_hash(*, rolling_summary_text: object) -> str | None:
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
        rolling_hash = _build_rolling_hash(rolling_summary_text=summary_text)
    version = rolling_payload.get("version")
    version_part = str(version) if version is not None else "na"
    if not rolling_hash:
        return None
    raw = f"{lead_id.strip()}:{version_part}:{rolling_hash.strip()}"
    return sha256(raw.encode("utf-8")).hexdigest()


def fetch_current_rolling_pointer(*, lead_id: str) -> Optional[Dict[str, Any]]:
    if not lead_id:
        return None
    client = get_firestore_client()
    if not client:
        return None
    pointer_ref = (
        _lead_memory_doc_ref(client=client, lead_id=lead_id)
        .collection(_ROLLING_CURRENT_POINTER_COLLECTION_NAME)
        .document(_ROLLING_CURRENT_POINTER_DOC_ID)
    )
    snapshot = safe_execute(pointer_ref.get)
    if snapshot and getattr(snapshot, "exists", False):
        return snapshot.to_dict() or {}
    return None


def fetch_rolling_artifact(*, lead_id: str, artifact_id: str) -> Optional[Dict[str, Any]]:
    if not lead_id or not artifact_id:
        return None
    client = get_firestore_client()
    if not client:
        return None
    artifact_ref = (
        _lead_memory_doc_ref(client=client, lead_id=lead_id)
        .collection(_ROLLING_ARTIFACTS_COLLECTION_NAME)
        .document(artifact_id)
    )
    snapshot = safe_execute(artifact_ref.get)
    if snapshot and getattr(snapshot, "exists", False):
        return snapshot.to_dict() or {}
    return None


def create_rolling_artifact(
    *,
    lead_id: str,
    artifact_id: str,
    artifact_payload: Dict[str, Any],
) -> bool:
    if not lead_id or not artifact_id:
        return False
    _ensure_memory_root_document(
        lead_id=lead_id,
        now=artifact_payload.get("updated_at") or datetime.now(tz=timezone.utc),
    )
    client = require_client_for_write()
    artifact_ref = (
        _lead_memory_doc_ref(client=client, lead_id=lead_id)
        .collection(_ROLLING_ARTIFACTS_COLLECTION_NAME)
        .document(artifact_id)
    )
    existing = safe_execute(artifact_ref.get)
    if existing and getattr(existing, "exists", False):
        return True
    payload = dict(artifact_payload or {})
    payload["artifact_id"] = artifact_id
    payload["lead_id"] = lead_id
    if "rolling_hash" not in payload or not str(payload.get("rolling_hash") or "").strip():
        payload["rolling_hash"] = _build_rolling_hash(rolling_summary_text=payload.get("rolling_summary_text"))
    try:
        safe_execute(artifact_ref.create, payload)
    except AlreadyExists:
        return True
    return True


def promote_rolling_pointer(
    *,
    lead_id: str,
    artifact_id: str,
    pointer_payload: Dict[str, Any],
) -> bool:
    if not lead_id or not artifact_id:
        return False
    client = require_client_for_write()
    pointer_ref = (
        _lead_memory_doc_ref(client=client, lead_id=lead_id)
        .collection(_ROLLING_CURRENT_POINTER_COLLECTION_NAME)
        .document(_ROLLING_CURRENT_POINTER_DOC_ID)
    )
    artifact_ref = (
        _lead_memory_doc_ref(client=client, lead_id=lead_id)
        .collection(_ROLLING_ARTIFACTS_COLLECTION_NAME)
        .document(artifact_id)
    )

    def _work(transaction) -> bool:
        artifact_snapshot = safe_execute(artifact_ref.get, transaction=transaction)
        if not artifact_snapshot or not getattr(artifact_snapshot, "exists", False):
            return False
        payload = dict(pointer_payload or {})
        payload["artifact_id"] = artifact_id
        payload["lead_id"] = lead_id
        safe_execute(transaction.set, pointer_ref, payload, merge=True)
        return True

    return bool(run_in_transaction(_work))


def update_rolling_summary(*, lead_id: str, rolling_update: Dict[str, Any], updated_at: datetime, extra_fields: Optional[Dict[str, Any]] = None) -> bool:
    if not lead_id:
        return False
    _ensure_memory_root_document(lead_id=lead_id, now=updated_at)
    client = require_client_for_write()
    pointer_ref = (
        client.collection(_LEAD_MEMORIES_COLLECTION_NAME)
        .document(lead_id)
        .collection(_ROLLING_CURRENT_POINTER_COLLECTION_NAME)
        .document(_ROLLING_CURRENT_POINTER_DOC_ID)
    )
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
        payload["rolling_hash"] = _build_rolling_hash(rolling_summary_text=payload.get("rolling_summary_text"))
    payload["created_at"] = updated_at
    if isinstance(extra_fields, dict):
        payload.update({key: value for key, value in extra_fields.items() if value is not None})
    artifact_id = build_rolling_artifact_id(lead_id=lead_id, rolling_payload=payload)
    if not artifact_id:
        return False
    artifact_payload = dict(payload)
    artifact_payload["created_at"] = payload.get("created_at") or updated_at
    artifact_created = create_rolling_artifact(
        lead_id=lead_id,
        artifact_id=artifact_id,
        artifact_payload=artifact_payload,
    )
    pointer_promoted = promote_rolling_pointer(
        lead_id=lead_id,
        artifact_id=artifact_id,
        pointer_payload={
            "updated_at": updated_at,
            "version": payload.get("version"),
            "rolling_hash": payload.get("rolling_hash"),
        },
    )
    write_materialized = bool(pointer_promoted and artifact_created)
    logger.info(
        "memory_rolling_write_diag_after",
        extra={
            "write_type": "rolling_summary_write",
            "resolved_document_path": _doc_path(pointer_ref),
            "write_completed_without_exception": True,
            "post_write_materialized": write_materialized,
        },
    )
    if not write_materialized:
        logger.warning(
            "memory_rolling_write_materialization_failed",
            extra={
                "write_type": "rolling_summary_write",
                "resolved_document_path": _doc_path(pointer_ref),
                "materialized": False,
            },
        )
        return False
    root_ref = _memory_root_ref(client=require_client_for_write(), lead_id=lead_id)
    safe_execute(
        root_ref.set,
        {"updated_at": updated_at, "version": _MEMORY_ROOT_VERSION, "lead_id": lead_id},
        merge=True,
    )
    logger.info(
        "memory_root_write_diag_after_rolling_summary",
        extra={
            "write_type": "memory_root_write",
            "resolved_document_path": _doc_path(root_ref),
            "write_completed_without_exception": True,
            "triggered_by_rolling_summary_write": True,
        },
    )
    return True
