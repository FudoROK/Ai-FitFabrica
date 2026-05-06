from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.adapters.database.firestore import event_state_machine as esm


class _Snapshot:
    def __init__(self, data: dict | None):
        self._data = data

    def to_dict(self):
        return dict(self._data) if self._data is not None else {}


class _DocRef:
    def __init__(self, storage: dict[str, dict], versions: dict[str, int], doc_id: str):
        self._storage = storage
        self._versions = versions
        self._doc_id = doc_id

    def create(self, payload):
        if self._doc_id in self._storage:
            raise esm.AlreadyExists("exists")
        self._storage[self._doc_id] = dict(payload)
        self._versions[self._doc_id] = 1

    def get(self, transaction=None):
        if transaction is not None:
            transaction._read_versions[self._doc_id] = self._versions.get(self._doc_id, 0)
        return _Snapshot(self._storage.get(self._doc_id))

    def set(self, payload, merge=False):
        current = dict(self._storage.get(self._doc_id, {})) if merge else {}
        current.update(payload)
        self._storage[self._doc_id] = current
        self._versions[self._doc_id] = self._versions.get(self._doc_id, 0) + 1


class _Collection:
    def __init__(self, storage: dict[str, dict], versions: dict[str, int]):
        self._storage = storage
        self._versions = versions

    def document(self, doc_id: str):
        return _DocRef(self._storage, self._versions, doc_id)


class _ConflictError(Exception):
    pass


class _Transaction:
    def __init__(self, versions: dict[str, int]):
        self._versions = versions
        self._read_versions: dict[str, int] = {}
        self._writes: list[tuple[_DocRef, dict, bool]] = []

    def set(self, doc_ref: _DocRef, payload: dict, merge=False):
        self._writes.append((doc_ref, dict(payload), merge))

    def commit(self):
        for doc_id, read_version in self._read_versions.items():
            if self._versions.get(doc_id, 0) != read_version:
                raise _ConflictError("write conflict")
        for doc_ref, payload, merge in self._writes:
            doc_ref.set(payload, merge=merge)


class _Client:
    def __init__(self):
        self.storage: dict[str, dict] = {}
        self.versions: dict[str, int] = {}

    def collection(self, _name: str):
        return _Collection(self.storage, self.versions)

    def transaction(self):
        return _Transaction(self.versions)


def test_transaction_contract_simulated_conflict_retries_and_yields_single_winner(monkeypatch):
    """Integration-style simulation of transaction contract (not emulator-backed).

    Models read-version conflict + retry, so callback is re-read on each retry.
    """

    client = _Client()
    now = datetime.now(timezone.utc)
    client.storage["telegram:tx"] = {
        "status": "processing",
        "attempt_count": 1,
        "processing_owner": "worker-a",
        "processing_owner_token": "token-a",
        "processing_started_at": now - timedelta(seconds=600),
        "processing_expires_at": now - timedelta(seconds=1),
        "updated_at": now - timedelta(seconds=600),
    }
    client.versions["telegram:tx"] = 1
    monkeypatch.setattr(esm, "require_client_for_write", lambda: client)

    injected = {"done": False}

    def _run_in_transaction(work):
        for _ in range(3):
            tx = client.transaction()
            result = work(tx)
            if not injected["done"]:
                injected["done"] = True
                client.collection("processed_pubsub_updates").document("telegram:tx").set(
                    {
                        "status": "processing",
                        "attempt_count": 2,
                        "processing_owner": "worker-z",
                        "processing_owner_token": "token-z",
                        "processing_started_at": now,
                        "processing_expires_at": now + timedelta(seconds=300),
                        "updated_at": now,
                    },
                    merge=True,
                )
            try:
                tx.commit()
                return result
            except _ConflictError:
                continue
        raise AssertionError("transaction retries exceeded")

    monkeypatch.setattr(esm, "run_in_transaction", _run_in_transaction)

    result = esm.start_normalized_event_processing(
        update_key="telegram:tx",
        channel="telegram",
        conversation_identity="42",
        event_identity="tx",
        owner="worker-b",
    )

    assert result.decision == "already_processing"
    assert client.storage["telegram:tx"]["processing_owner"] == "worker-z"
    assert client.storage["telegram:tx"]["attempt_count"] == 2
