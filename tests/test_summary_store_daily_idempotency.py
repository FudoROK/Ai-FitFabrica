from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.database.firestore import summary_store as store


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
        if transaction is not None and getattr(transaction, "wrote", False):
            raise AssertionError("transaction attempted read after write")
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


class _Client:
    def __init__(self):
        self.data: dict[str, dict] = {}

    def collection(self, name: str):
        assert name == "lead_memories"
        return _Collection(self.data)


class _Txn:
    def __init__(self):
        self.wrote = False

    def set(self, doc_ref, payload, merge: bool = False):
        self.wrote = True
        doc_ref.set(payload, merge=merge)


def _setup(monkeypatch, client: _Client):
    monkeypatch.setattr(store, "get_firestore_client", lambda: client)
    monkeypatch.setattr(store, "require_client_for_write", lambda: client)
    monkeypatch.setattr(store, "safe_execute", lambda fn, *args, **kwargs: fn(*args, **kwargs))
    monkeypatch.setattr(store, "run_in_transaction", lambda work: work(_Txn()))


def test_write_daily_summary_returns_true_for_idempotent_same_payload(monkeypatch):
    client = _Client()
    _setup(monkeypatch, client)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = store.write_daily_summary(
        lead_id="lead-1",
        memory_day_key="2026-01-01",
        summary_text="daily",
        open_questions=[],
        carry_forward_notes=[],
        learned_facts=[],
        changed_facts=[],
        memory_relevance_flags=[],
        created_at=now,
    )
    second = store.write_daily_summary(
        lead_id="lead-1",
        memory_day_key="2026-01-01",
        summary_text="daily",
        open_questions=[],
        carry_forward_notes=[],
        learned_facts=[],
        changed_facts=[],
        memory_relevance_flags=[],
        created_at=now,
    )

    assert first is True
    assert second is True


def test_write_daily_summary_returns_false_on_existing_payload_mismatch(monkeypatch):
    client = _Client()
    _setup(monkeypatch, client)
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = store.write_daily_summary(
        lead_id="lead-1",
        memory_day_key="2026-01-01",
        summary_text="daily-v1",
        open_questions=[],
        carry_forward_notes=[],
        learned_facts=[],
        changed_facts=[],
        memory_relevance_flags=[],
        created_at=now,
    )
    second = store.write_daily_summary(
        lead_id="lead-1",
        memory_day_key="2026-01-01",
        summary_text="daily-v2",
        open_questions=[],
        carry_forward_notes=[],
        learned_facts=[],
        changed_facts=[],
        memory_relevance_flags=[],
        created_at=now,
    )

    assert first is True
    assert second is False
