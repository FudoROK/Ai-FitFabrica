from __future__ import annotations

from typing import Optional

from src.adapters.database.firestore.firestore_client_factory import firestore
from src.adapters.database.firestore.firestore_client_factory import get_firestore_client, safe_execute
from src.adapters.database.firestore.firestore_async_executor import run_blocking
from .models import ActiveWindowRecord, ConversationStateRecord

_ACTIVE_WINDOWS_COLLECTION = "memory_active_windows"
_CONVERSATION_STATE_COLLECTION = "memory_conversation_states"


def _fetch_active_window(lead_id: str) -> ActiveWindowRecord | None:
    client = get_firestore_client()
    if not client:
        return None
    snapshot = safe_execute(client.collection(_ACTIVE_WINDOWS_COLLECTION).document(str(lead_id)).get)
    if not snapshot or not snapshot.exists:
        return None
    return ActiveWindowRecord(**(snapshot.to_dict() or {}))


def _list_active_windows(statuses: list[str] | None = None) -> list[ActiveWindowRecord]:
    client = get_firestore_client()
    if not client:
        return []
    if firestore is None:  # pragma: no cover
        return []

    normalized_statuses = [str(status).strip() for status in statuses or [] if str(status).strip()]
    if not normalized_statuses:
        docs = safe_execute(client.collection(_ACTIVE_WINDOWS_COLLECTION).stream)
        return [ActiveWindowRecord(**(doc.to_dict() or {})) for doc in (docs or [])]

    records: list[ActiveWindowRecord] = []
    seen_lead_ids: set[str] = set()
    for status in normalized_statuses:
        query = client.collection(_ACTIVE_WINDOWS_COLLECTION).where(
            filter=firestore.FieldFilter("window_status", "==", status)
        )
        docs = safe_execute(query.stream) or []
        for doc in docs:
            payload = doc.to_dict() or {}
            lead_id = str(payload.get("lead_id") or doc.id)
            if lead_id in seen_lead_ids:
                continue
            seen_lead_ids.add(lead_id)
            records.append(ActiveWindowRecord(**payload))
    return records


def _store_active_window(window: ActiveWindowRecord) -> ActiveWindowRecord:
    client = get_firestore_client()
    if not client:
        return window
    doc_ref = client.collection(_ACTIVE_WINDOWS_COLLECTION).document(str(window.lead_id))
    safe_execute(doc_ref.set, window.model_dump(mode="python"), merge=True)
    snapshot = safe_execute(doc_ref.get)
    if not snapshot or not snapshot.exists:
        return window
    return ActiveWindowRecord(**(snapshot.to_dict() or {}))


def _fetch_conversation_state(lead_id: str) -> ConversationStateRecord | None:
    client = get_firestore_client()
    if not client:
        return None
    snapshot = safe_execute(client.collection(_CONVERSATION_STATE_COLLECTION).document(str(lead_id)).get)
    if not snapshot or not snapshot.exists:
        return None
    return ConversationStateRecord(**(snapshot.to_dict() or {}))


def _store_conversation_state(state: ConversationStateRecord) -> ConversationStateRecord:
    client = get_firestore_client()
    if not client:
        return state
    doc_ref = client.collection(_CONVERSATION_STATE_COLLECTION).document(str(state.lead_id))
    safe_execute(doc_ref.set, state.model_dump(mode="python"), merge=True)
    snapshot = safe_execute(doc_ref.get)
    if not snapshot or not snapshot.exists:
        return state
    return ConversationStateRecord(**(snapshot.to_dict() or {}))


def _delete_conversation_state(lead_id: str) -> None:
    client = get_firestore_client()
    if not client:
        return
    doc_ref = client.collection(_CONVERSATION_STATE_COLLECTION).document(str(lead_id))
    safe_execute(doc_ref.delete)


class FirestoreMemoryLayerRepository:
    async def list_active_windows(
        self,
        *,
        statuses: list[str] | None = None,
    ) -> list[ActiveWindowRecord]:
        return await run_blocking(_list_active_windows, statuses)

    async def get_active_window(self, *, lead_id: str) -> ActiveWindowRecord | None:
        return await run_blocking(_fetch_active_window, lead_id)

    async def upsert_active_window(self, *, window: ActiveWindowRecord) -> ActiveWindowRecord:
        return await run_blocking(_store_active_window, window)

    async def get_conversation_state(self, *, lead_id: str) -> ConversationStateRecord | None:
        return await run_blocking(_fetch_conversation_state, lead_id)

    async def upsert_conversation_state(self, *, state: ConversationStateRecord) -> ConversationStateRecord:
        return await run_blocking(_store_conversation_state, state)

    async def delete_conversation_state(self, *, lead_id: str) -> None:
        await run_blocking(_delete_conversation_state, lead_id)


class InMemoryMemoryLayerRepository:
    def __init__(self) -> None:
        self._active_windows: dict[str, ActiveWindowRecord] = {}
        self._conversation_states: dict[str, ConversationStateRecord] = {}

    async def list_active_windows(
        self,
        *,
        statuses: list[str] | None = None,
    ) -> list[ActiveWindowRecord]:
        normalized_statuses = {str(status).strip() for status in statuses or [] if str(status).strip()}
        records = list(self._active_windows.values())
        if not normalized_statuses:
            return records
        return [record for record in records if record.window_status in normalized_statuses]

    async def get_active_window(self, *, lead_id: str) -> ActiveWindowRecord | None:
        return self._active_windows.get(str(lead_id))

    async def upsert_active_window(self, *, window: ActiveWindowRecord) -> ActiveWindowRecord:
        self._active_windows[str(window.lead_id)] = window
        return window

    async def get_conversation_state(self, *, lead_id: str) -> ConversationStateRecord | None:
        return self._conversation_states.get(str(lead_id))

    async def upsert_conversation_state(self, *, state: ConversationStateRecord) -> ConversationStateRecord:
        self._conversation_states[str(state.lead_id)] = state
        return state

    async def delete_conversation_state(self, *, lead_id: str) -> None:
        self._conversation_states.pop(str(lead_id), None)
