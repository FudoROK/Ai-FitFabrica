"""Lead summary persistence helpers."""
from __future__ import annotations

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
from .summary_store_core import (
    doc_path as _doc_path,
    lead_memory_doc_ref as _lead_memory_doc_ref,
    memory_root_ref as _memory_root_ref,
    rolling_pointer_read_enabled as _rolling_pointer_read_enabled,
)
from .summary_store_daily import (
    acquire_memory_write_guard as _acquire_memory_write_guard,
    fetch_daily_summary as _fetch_daily_summary,
    fetch_latest_daily_summary as _fetch_latest_daily_summary,
    release_memory_write_guard as _release_memory_write_guard,
    write_daily_summary as _write_daily_summary,
)
from .summary_store_rolling import (
    build_rolling_artifact_id,
    create_rolling_artifact as _create_rolling_artifact,
    fetch_current_rolling_pointer as _fetch_current_rolling_pointer,
    fetch_rolling_artifact as _fetch_rolling_artifact,
    fetch_rolling_summary as _fetch_rolling_summary,
    is_canonical_rolling_payload as _is_canonical_rolling_payload,
    promote_rolling_pointer as _promote_rolling_pointer,
    update_rolling_summary as _update_rolling_summary,
)


def _ensure_memory_root_document(*, lead_id: str, now) -> None:
    client = require_client_for_write()
    root_ref = _memory_root_ref(client=client, lead_id=lead_id)
    existing = safe_execute(root_ref.get)
    if existing and getattr(existing, "exists", False):
        safe_execute(root_ref.set, {"lead_id": lead_id, "updated_at": now, "version": 1}, merge=True)
        return
    safe_execute(
        root_ref.set,
        {
            "lead_id": lead_id,
            "created_at": now,
            "updated_at": now,
            "version": 1,
        },
        merge=True,
    )


def fetch_latest_daily_summary(lead_id: str):
    return _fetch_latest_daily_summary(
        lead_id,
        firestore_sdk=firestore,
        get_client=get_firestore_client,
        safe_execute_fn=safe_execute,
    )


def fetch_daily_summary(lead_id: str, memory_day_key: str):
    return _fetch_daily_summary(
        lead_id,
        memory_day_key,
        get_client=get_firestore_client,
        safe_execute_fn=safe_execute,
    )


def write_daily_summary(**kwargs):
    return _write_daily_summary(
        **kwargs,
        ensure_root_document=_ensure_memory_root_document,
        get_writer=require_client_for_write,
        safe_execute_fn=safe_execute,
    )


def acquire_memory_write_guard(*, lead_id: str, idempotency_key: str, created_at):
    return _acquire_memory_write_guard(
        lead_id=lead_id,
        idempotency_key=idempotency_key,
        created_at=created_at,
        ensure_root_document=_ensure_memory_root_document,
        get_writer=require_client_for_write,
        safe_execute_fn=safe_execute,
        run_transaction=run_in_transaction,
    )


def release_memory_write_guard(*, lead_id: str, idempotency_key: str) -> None:
    _release_memory_write_guard(
        lead_id=lead_id,
        idempotency_key=idempotency_key,
        get_writer=require_client_for_write,
        safe_execute_fn=safe_execute,
    )


def create_rolling_artifact(*, lead_id: str, artifact_id: str, artifact_payload, already_exists_error=None):
    return _create_rolling_artifact(
        lead_id=lead_id,
        artifact_id=artifact_id,
        artifact_payload=artifact_payload,
        already_exists_error=already_exists_error or AlreadyExists,
        ensure_root_document=_ensure_memory_root_document,
        get_writer=require_client_for_write,
        safe_execute_fn=safe_execute,
    )


def fetch_current_rolling_pointer(*, lead_id: str):
    return _fetch_current_rolling_pointer(
        lead_id=lead_id,
        get_client=get_firestore_client,
        safe_execute_fn=safe_execute,
    )


def fetch_rolling_artifact(*, lead_id: str, artifact_id: str):
    return _fetch_rolling_artifact(
        lead_id=lead_id,
        artifact_id=artifact_id,
        get_client=get_firestore_client,
        safe_execute_fn=safe_execute,
    )


def fetch_rolling_summary(*, lead_id: str):
    return _fetch_rolling_summary(
        lead_id=lead_id,
        get_client=get_firestore_client,
        pointer_reads_enabled=_rolling_pointer_read_enabled,
        fetch_pointer=fetch_current_rolling_pointer,
        fetch_artifact=fetch_rolling_artifact,
    )


def promote_rolling_pointer(*, lead_id: str, artifact_id: str, pointer_payload):
    return _promote_rolling_pointer(
        lead_id=lead_id,
        artifact_id=artifact_id,
        pointer_payload=pointer_payload,
        get_writer=require_client_for_write,
        safe_execute_fn=safe_execute,
        run_transaction=run_in_transaction,
    )


def update_rolling_summary(*, lead_id: str, rolling_update, updated_at, extra_fields=None):
    return _update_rolling_summary(
        lead_id=lead_id,
        rolling_update=rolling_update,
        updated_at=updated_at,
        extra_fields=extra_fields,
        already_exists_error=AlreadyExists,
        ensure_root_document=_ensure_memory_root_document,
        get_writer=require_client_for_write,
        safe_execute_fn=safe_execute,
        create_artifact_fn=create_rolling_artifact,
        promote_pointer_fn=promote_rolling_pointer,
    )


__all__ = [
    "AlreadyExists",
    "_doc_path",
    "_ensure_memory_root_document",
    "_is_canonical_rolling_payload",
    "_lead_memory_doc_ref",
    "_memory_root_ref",
    "_rolling_pointer_read_enabled",
    "acquire_memory_write_guard",
    "build_rolling_artifact_id",
    "create_rolling_artifact",
    "fetch_current_rolling_pointer",
    "fetch_daily_summary",
    "fetch_latest_daily_summary",
    "fetch_rolling_artifact",
    "fetch_rolling_summary",
    "get_firestore_client",
    "promote_rolling_pointer",
    "require_client_for_write",
    "release_memory_write_guard",
    "run_in_transaction",
    "safe_execute",
    "update_rolling_summary",
    "write_daily_summary",
]
