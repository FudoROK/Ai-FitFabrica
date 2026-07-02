"""Shared Firestore memory-summary storage helpers."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from src.settings import load_settings

from .firestore_client_factory import (
    get_firestore_client,
    require_client_for_write,
    safe_execute,
)

logger = logging.getLogger(__name__)

LEAD_MEMORIES_COLLECTION_NAME = "lead_memories"
MEMORY_ROOT_VERSION = 1
ROLLING_ARTIFACTS_COLLECTION_NAME = "rolling_artifacts"
ROLLING_CURRENT_POINTER_COLLECTION_NAME = "rolling_current"
ROLLING_CURRENT_POINTER_DOC_ID = "current"


def memory_root_ref(*, client, lead_id: str):
    return client.collection(LEAD_MEMORIES_COLLECTION_NAME).document(lead_id)


def lead_memory_doc_ref(*, client, lead_id: str):
    return client.collection(LEAD_MEMORIES_COLLECTION_NAME).document(lead_id)


def doc_path(doc_ref: Any) -> str:
    path = getattr(doc_ref, "path", None)
    if isinstance(path, str) and path:
        return path
    return str(doc_ref)


def rolling_settings():
    try:
        return load_settings()
    except Exception:  # pragma: no cover - defensive fallback for isolated tests
        return None


def rolling_pointer_read_enabled() -> bool:
    settings = rolling_settings()
    if settings is None:
        return True
    return bool(getattr(settings, "memory_rolling_pointer_read_enabled", True))


def ensure_memory_root_document(*, lead_id: str, now: datetime) -> None:
    client = require_client_for_write()
    root_ref = memory_root_ref(client=client, lead_id=lead_id)
    existing = safe_execute(root_ref.get)
    if existing and getattr(existing, "exists", False):
        safe_execute(root_ref.set, {"lead_id": lead_id, "updated_at": now, "version": MEMORY_ROOT_VERSION}, merge=True)
        return
    safe_execute(
        root_ref.set,
        {
            "lead_id": lead_id,
            "created_at": now,
            "updated_at": now,
            "version": MEMORY_ROOT_VERSION,
        },
        merge=True,
    )


__all__ = [
    "LEAD_MEMORIES_COLLECTION_NAME",
    "MEMORY_ROOT_VERSION",
    "ROLLING_ARTIFACTS_COLLECTION_NAME",
    "ROLLING_CURRENT_POINTER_COLLECTION_NAME",
    "ROLLING_CURRENT_POINTER_DOC_ID",
    "doc_path",
    "ensure_memory_root_document",
    "get_firestore_client",
    "lead_memory_doc_ref",
    "logger",
    "memory_root_ref",
    "require_client_for_write",
    "rolling_pointer_read_enabled",
    "safe_execute",
]
