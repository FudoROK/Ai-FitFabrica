from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.database.firestore import summary_store as store
from src.memory_layer.services.memory_sync_persistence_service import MemorySyncPersistenceService


class _Snapshot:
    def __init__(self, exists: bool, payload: dict | None = None):
        self.exists = exists
        self._payload = payload or {}

    def to_dict(self):
        return dict(self._payload)


class _DocRef:
    def __init__(self, bucket: dict[str, dict], doc_id: str):
        self._bucket = bucket
        self._doc_id = doc_id

    def get(self, transaction=None):
        payload = self._bucket.get(self._doc_id)
        if payload is None:
            return _Snapshot(False)
        return _Snapshot(True, payload)

    def set(self, payload, merge: bool = False):
        if merge and self._doc_id in self._bucket:
            self._bucket[self._doc_id] = {**self._bucket[self._doc_id], **dict(payload)}
        else:
            self._bucket[self._doc_id] = dict(payload)

    def create(self, payload):
        if self._doc_id in self._bucket:
            raise store.AlreadyExists("exists")
        self._bucket[self._doc_id] = dict(payload)


class _Collection:
    def __init__(self, docs: dict[str, dict]):
        self._docs = docs

    def document(self, doc_id: str):
        return _LeadMemoryDoc(self._docs.setdefault(doc_id, {}))


class _SubCollection:
    def __init__(self, docs: dict[str, dict]):
        self._docs = docs

    def document(self, doc_id: str):
        return _DocRef(self._docs, doc_id)


class _LeadMemoryDoc:
    def __init__(self, state: dict[str, dict]):
        self._state = state

    def collection(self, name: str):
        return _SubCollection(self._state.setdefault(name, {}))

    def get(self):
        return _Snapshot(bool(self._state), self._state)

    def set(self, payload, merge: bool = False):
        if merge:
            self._state.update(dict(payload))
        else:
            self._state.clear()
            self._state.update(dict(payload))


class _Txn:
    def set(self, doc_ref, payload, merge: bool = False):
        doc_ref.set(payload, merge=merge)


class _Client:
    def __init__(self):
        self.data: dict[str, dict] = {}

    def collection(self, name: str):
        assert name == "lead_memories"
        return _Collection(self.data)

    def transaction(self):
        return _Txn()


def _setup(monkeypatch, client: _Client):
    monkeypatch.setattr(store, "get_firestore_client", lambda: client)
    monkeypatch.setattr(store, "require_client_for_write", lambda: client)
    monkeypatch.setattr(store, "safe_execute", lambda fn, *args, **kwargs: fn(*args, **kwargs))
    monkeypatch.setattr(store, "run_in_transaction", lambda work: work(_Txn()))


def test_pointer_read_returns_none_when_pointer_targets_missing_artifact(monkeypatch):
    client = _Client()
    _setup(monkeypatch, client)
    monkeypatch.setattr(store, "_rolling_pointer_read_enabled", lambda: True)

    store.update_rolling_summary(
        lead_id="lead-1",
        rolling_update={
            "rolling_summary_text": "valid rolling",
            "open_questions": [],
            "carry_forward_notes": [],
            "days_count": 1,
            "last_daily_summary_date": "2026-01-01",
            "version": 1,
        },
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    client.data["lead-1"]["rolling_current"]["current"] = {"artifact_id": "missing-artifact"}

    payload = store.fetch_rolling_summary(lead_id="lead-1")

    assert payload is None


def test_update_persists_pointer_and_artifact_without_legacy_doc(monkeypatch):
    client = _Client()
    _setup(monkeypatch, client)

    ok = store.update_rolling_summary(
        lead_id="lead-1",
        rolling_update={
            "rolling_summary_text": "клиент подтвердил интерес и бюджет",
            "open_questions": ["q"],
            "carry_forward_notes": [],
            "days_count": 2,
            "last_daily_summary_date": "2026-01-02",
            "version": 2,
        },
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    assert ok is True
    lead_data = client.data["lead-1"]
    assert "rolling_summaries" not in lead_data
    pointer = lead_data["rolling_current"]["current"]
    assert pointer["artifact_id"] in lead_data["rolling_artifacts"]


def test_update_is_rollback_safe_when_pointer_promotion_fails(monkeypatch):
    client = _Client()
    _setup(monkeypatch, client)
    monkeypatch.setattr(store, "promote_rolling_pointer", lambda **_kwargs: False)

    ok = store.update_rolling_summary(
        lead_id="lead-1",
        rolling_update={
            "rolling_summary_text": "клиент согласовал демонстрацию и бюджет",
            "open_questions": [],
            "carry_forward_notes": [],
            "days_count": 3,
            "last_daily_summary_date": "2026-01-03",
            "version": 3,
        },
        updated_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
    )

    assert ok is False
    assert "rolling_summaries" not in client.data["lead-1"]


def test_canary_confirmed_validation_no_version_mismatch(monkeypatch):
    class _Repo:
        async def fetch_rolling_summary(self, *, lead_id: str):
            return {
                "rolling_summary_text": "клиент подтвердил договоренности на неделе",
                "version": 7,
                "rolling_hash": "hash-7",
            }

    service = MemorySyncPersistenceService(leads_repo=_Repo())

    import asyncio

    result = asyncio.run(
        service.fetch_confirmed_rolling_summary_validation(
            lead_id="lead-1",
            expected_rolling_version=7,
            expected_rolling_hash="hash-7",
        )
    )

    assert result.ok is True
    assert result.reason_code is None
