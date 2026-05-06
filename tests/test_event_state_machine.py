from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.adapters.database.firestore import event_state_machine as esm


class _Snapshot:
    def __init__(self, data: dict | None):
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data is not None else {}


class _DocRef:
    def __init__(self, storage: dict[str, dict], doc_id: str):
        self._storage = storage
        self._doc_id = doc_id

    def create(self, payload):
        if self._doc_id in self._storage:
            raise esm.AlreadyExists("exists")
        self._storage[self._doc_id] = dict(payload)

    def get(self, transaction=None):
        return _Snapshot(self._storage.get(self._doc_id))

    def set(self, payload, merge=False):
        if merge and self._doc_id in self._storage:
            next_payload = dict(self._storage[self._doc_id])
            next_payload.update(payload)
            self._storage[self._doc_id] = next_payload
            return
        self._storage[self._doc_id] = dict(payload)


class _Collection:
    def __init__(self, storage: dict[str, dict]):
        self._storage = storage

    def document(self, doc_id: str):
        return _DocRef(self._storage, doc_id)


class _Transaction:
    def __init__(self):
        self._writes: list[tuple[_DocRef, dict, bool]] = []
        self._rolled_back = False

    def get(self, doc_ref: _DocRef):
        return doc_ref.get()

    def set(self, doc_ref: _DocRef, payload: dict, merge=False):
        self._writes.append((doc_ref, dict(payload), merge))

    def rollback(self):
        self._rolled_back = True
        self._writes = []

    def commit(self):
        if self._rolled_back:
            return
        for doc_ref, payload, merge in self._writes:
            doc_ref.set(payload, merge=merge)


class _Client:
    def __init__(self):
        self.storage: dict[str, dict] = {}

    def collection(self, _name: str):
        return _Collection(self.storage)

    def transaction(self):
        return _Transaction()


def _install_transaction_runner(monkeypatch):
    def _run_in_transaction(work):
        transaction = esm.require_client_for_write().transaction()
        result = work(transaction)
        transaction.commit()
        return result

    monkeypatch.setattr(esm, "run_in_transaction", _run_in_transaction)


def _install_lease_defaults(monkeypatch, *, lease_seconds: int = 300, stale_seconds: int = 300):
    monkeypatch.setattr(esm, "_lease_duration_seconds", lambda: lease_seconds)
    monkeypatch.setattr(esm, "_stale_reclaim_seconds", lambda: stale_seconds)


def test_start_on_new_event_sets_processing_lease_and_owner_token(monkeypatch):
    client = _Client()
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)
    _install_transaction_runner(monkeypatch)
    _install_lease_defaults(monkeypatch)

    result = esm.start_normalized_event_processing(
        update_key="telegram:101",
        channel="telegram",
        conversation_identity="42",
        event_identity="101",
        owner="worker-a",
    )

    state = client.storage["telegram:101"]
    assert result.decision == "started"
    assert state["status"] == "processing"
    assert state["processing_owner"] == "worker-a"
    assert state["processing_owner_token"]
    assert result.owner_token == state["processing_owner_token"]
    assert state["attempt_count"] == 1


def test_lease_renewal_keeps_event_alive_and_blocks_reclaim(monkeypatch):
    client = _Client()
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)
    _install_transaction_runner(monkeypatch)
    _install_lease_defaults(monkeypatch, lease_seconds=30)

    started = esm.start_normalized_event_processing(
        update_key="telegram:renew",
        channel="telegram",
        conversation_identity="42",
        event_identity="renew",
        owner="worker-a",
    )

    renewed = esm.renew_normalized_event_processing_lease("telegram:renew", owner_token=str(started.owner_token))
    assert renewed is True

    blocked = esm.start_normalized_event_processing(
        update_key="telegram:renew",
        channel="telegram",
        conversation_identity="42",
        event_identity="renew",
        owner="worker-b",
    )
    assert blocked.decision == "already_processing"


def test_expired_lease_reclaims_with_new_token_and_old_token_cannot_complete_or_fail(monkeypatch):
    client = _Client()
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)
    _install_transaction_runner(monkeypatch)
    _install_lease_defaults(monkeypatch, lease_seconds=5)

    first = esm.start_normalized_event_processing(
        update_key="telegram:reclaim",
        channel="telegram",
        conversation_identity="42",
        event_identity="reclaim",
        owner="worker-a",
    )
    client.storage["telegram:reclaim"]["processing_expires_at"] = datetime.now(timezone.utc) - timedelta(seconds=1)

    second = esm.start_normalized_event_processing(
        update_key="telegram:reclaim",
        channel="telegram",
        conversation_identity="42",
        event_identity="reclaim",
        owner="worker-b",
    )

    assert second.decision == "reclaimed"
    assert second.owner_token != first.owner_token
    assert esm.complete_normalized_event_processing("telegram:reclaim", owner_token=str(first.owner_token)) is False
    assert esm.fail_normalized_event_processing("telegram:reclaim", owner_token=str(first.owner_token), error="old") is False
    assert esm.complete_normalized_event_processing("telegram:reclaim", owner_token=str(second.owner_token)) is True


def test_completion_and_failure_require_valid_ownership_token(monkeypatch):
    client = _Client()
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)
    _install_transaction_runner(monkeypatch)
    _install_lease_defaults(monkeypatch)

    started = esm.start_normalized_event_processing(
        update_key="telegram:token",
        channel="telegram",
        conversation_identity="42",
        event_identity="token",
        owner="worker-a",
    )

    assert esm.fail_normalized_event_processing("telegram:token", owner_token="wrong", error="boom") is False
    assert esm.complete_normalized_event_processing("telegram:token", owner_token="wrong") is False
    assert esm.fail_normalized_event_processing("telegram:token", owner_token=str(started.owner_token), error="boom") is True


def test_completed_event_cannot_be_reclaimed(monkeypatch):
    client = _Client()
    now = datetime.now(timezone.utc)
    client.storage["telegram:106"] = {
        "status": "completed",
        "attempt_count": 4,
        "processing_started_at": now - timedelta(seconds=600),
        "processing_expires_at": now - timedelta(seconds=1),
        "processing_owner": "worker-a",
        "processing_owner_token": "old",
        "updated_at": now - timedelta(seconds=600),
    }
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)
    _install_transaction_runner(monkeypatch)
    _install_lease_defaults(monkeypatch)

    result = esm.start_normalized_event_processing(
        update_key="telegram:106",
        channel="telegram",
        conversation_identity="42",
        event_identity="106",
        owner="worker-b",
    )

    assert result.decision == "already_completed"


def test_step_completion_registry_is_stable_and_readable(monkeypatch):
    client = _Client()
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)
    _install_transaction_runner(monkeypatch)
    _install_lease_defaults(monkeypatch)

    started = esm.start_normalized_event_processing(
        update_key="telegram:steps",
        channel="telegram",
        conversation_identity="42",
        event_identity="steps",
        owner="worker-a",
    )

    assert esm.is_processing_step_completed("telegram:steps", step_key="telegram_send_reply") is False
    marked = esm.mark_processing_step_completed(
        "telegram:steps",
        owner_token=str(started.owner_token),
        step_key="telegram_send_reply",
        metadata={"channel": "telegram"},
    )
    assert marked is True
    assert esm.is_processing_step_completed("telegram:steps", step_key="telegram_send_reply") is True


def test_legacy_attempts_field_is_still_readable(monkeypatch):
    client = _Client()
    now = datetime.now(timezone.utc)
    client.storage["telegram:107"] = {
        "status": "processing",
        "attempts": 5,
        "processing_started_at": now - timedelta(seconds=600),
        "processing_expires_at": now - timedelta(seconds=1),
        "updated_at": now - timedelta(seconds=600),
    }
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)
    _install_transaction_runner(monkeypatch)
    _install_lease_defaults(monkeypatch)

    result = esm.start_normalized_event_processing(
        update_key="telegram:107",
        channel="telegram",
        conversation_identity="42",
        event_identity="107",
        owner="worker-b",
    )

    assert result.decision == "reclaimed"
    assert result.attempt_count == 6
    assert client.storage["telegram:107"]["attempt_count"] == 6
