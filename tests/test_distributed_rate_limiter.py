from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from src.services.dialog.dialog_service import DialogService
from src.services.rate_limit import FailModeRateLimiter, FirestoreRateLimiter, RateLimitDecision


class _FakeSnapshot:
    def __init__(self, payload):
        self._payload = payload
        self.exists = payload is not None

    def to_dict(self):
        return dict(self._payload or {})


class _FakeTransaction:
    def set(self, doc_ref, data, merge=True):
        doc_ref.set(data, merge=merge)


class _FakeDocRef:
    def __init__(self, storage: dict[str, dict], doc_id: str):
        self._storage = storage
        self._doc_id = doc_id

    def get(self, transaction=None):
        return _FakeSnapshot(self._storage.get(self._doc_id))

    def set(self, data, merge=True):
        if merge and self._doc_id in self._storage:
            self._storage[self._doc_id] = {**self._storage[self._doc_id], **data}
        else:
            self._storage[self._doc_id] = dict(data)


class _FakeCollection:
    def __init__(self, storage: dict[str, dict]):
        self._storage = storage

    def document(self, doc_id: str):
        return _FakeDocRef(self._storage, doc_id)


class _FakeFirestoreClient:
    def __init__(self, shared_storage: dict[str, dict]):
        self._shared_storage = shared_storage

    def collection(self, _name: str):
        return _FakeCollection(self._shared_storage)

    def transaction(self):
        return _FakeTransaction()


class _BrokenLimiter:
    def allow(self, key: str) -> RateLimitDecision:
        raise RuntimeError(f"broken limiter for {key}")


class _AllowLimiter:
    def allow(self, key: str) -> RateLimitDecision:
        return RateLimitDecision(status="allowed")


def _fake_transaction_runner(client, work):
    return work(client.transaction())


def test_firestore_rate_limiter_shared_state_between_instances():
    shared = {}
    client = _FakeFirestoreClient(shared)

    limiter_a = FirestoreRateLimiter(
        firestore_client=client,
        max_events=2,
        window_seconds=60,
        transaction_runner=_fake_transaction_runner,
    )
    limiter_b = FirestoreRateLimiter(
        firestore_client=client,
        max_events=2,
        window_seconds=60,
        transaction_runner=_fake_transaction_runner,
    )

    assert limiter_a.allow("lead-shared").status == "allowed"
    assert limiter_b.allow("lead-shared").status == "allowed"
    denied = limiter_a.allow("lead-shared")

    assert denied.status == "denied_limit_exceeded"
    assert denied.retry_after_seconds is not None


def test_firestore_rate_limiter_resets_window_from_storage_data():
    shared = {}
    client = _FakeFirestoreClient(shared)
    limiter = FirestoreRateLimiter(
        firestore_client=client,
        max_events=1,
        window_seconds=60,
        transaction_runner=_fake_transaction_runner,
    )

    key = "lead-reset"
    doc_id = limiter._doc_id(key)  # test helper for deterministic key
    shared[doc_id] = {
        "key": key,
        "window_start": datetime.now(timezone.utc) - timedelta(seconds=61),
        "count": 100,
    }

    decision = limiter.allow(key)
    assert decision.status == "allowed"
    assert shared[doc_id]["count"] == 1


def test_firestore_rate_limiter_executes_callback_via_transaction_runner():
    shared = {}
    client = _FakeFirestoreClient(shared)
    runner_calls: list[str] = []

    def _runner(client_arg, work):
        runner_calls.append("called")
        return work(client_arg.transaction())

    limiter = FirestoreRateLimiter(
        firestore_client=client,
        max_events=1,
        window_seconds=60,
        transaction_runner=_runner,
    )
    decision = limiter.allow("lead-runner")
    assert decision.status == "allowed"
    assert runner_calls == ["called"]


def test_rate_limiter_fail_open_on_backend_failure():
    limiter = FailModeRateLimiter(limiter=_BrokenLimiter(), fail_mode="open")

    decision = limiter.allow("lead-fail-open")

    assert decision.status == "backend_error"
    assert decision.reason == "rate_limiter_backend_failure"


def test_rate_limiter_fail_closed_on_backend_failure():
    limiter = FailModeRateLimiter(limiter=_BrokenLimiter(), fail_mode="closed")

    decision = limiter.allow("lead-fail-closed")

    assert decision.status == "backend_error"
    assert decision.reason == "rate_limiter_backend_failure"


def test_rate_limiter_defaults_to_fail_closed_on_backend_failure():
    limiter = FailModeRateLimiter(limiter=_BrokenLimiter())

    decision = limiter.allow("lead-default-fail-closed")

    assert decision.status == "backend_error"
    assert decision.reason == "rate_limiter_backend_failure"


def test_dialog_service_uses_injected_limiter():
    service = DialogService(
        messaging=object(),
        leads_repo=object(),
        sessions_repo=object(),
        settings=SimpleNamespace(environment="test"),
        rate_limiter=_AllowLimiter(),
    )

    assert isinstance(service.rate_limiter, _AllowLimiter)
