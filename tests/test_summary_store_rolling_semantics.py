from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.database.firestore import summary_store as store


def test_fetch_rolling_summary_returns_none_when_pointer_absent(monkeypatch):
    monkeypatch.setattr(store, "get_firestore_client", lambda: object())
    monkeypatch.setattr(store, "fetch_current_rolling_pointer", lambda **_kwargs: None)

    payload = store.fetch_rolling_summary(lead_id="lead-1")

    assert payload is None


def test_fetch_rolling_summary_rejects_placeholder_payload(monkeypatch):
    monkeypatch.setattr(store, "get_firestore_client", lambda: object())
    monkeypatch.setattr(store, "fetch_current_rolling_pointer", lambda **_kwargs: {"artifact_id": "artifact-1"})
    monkeypatch.setattr(
        store,
        "fetch_rolling_artifact",
        lambda **_kwargs: {"rolling_summary_text": "{{ROLLING_SUMMARY}}", "version": 1, "days_count": 1},
    )

    payload = store.fetch_rolling_summary(lead_id="lead-1")

    assert payload is None


def test_fetch_rolling_summary_accepts_pointer_artifact_payload(monkeypatch):
    monkeypatch.setattr(store, "get_firestore_client", lambda: object())
    monkeypatch.setattr(store, "fetch_current_rolling_pointer", lambda **_kwargs: {"artifact_id": "artifact-1"})
    monkeypatch.setattr(
        store,
        "fetch_rolling_artifact",
        lambda **_kwargs: {
            "rolling_summary_text": "Клиент ведёт согласование договора и ожидает финальную смету.",
            "version": 1,
            "days_count": 3,
        },
    )

    payload = store.fetch_rolling_summary(lead_id="lead-1")

    assert payload is not None
    assert payload["rolling_summary_text"].startswith("Клиент ведёт")


def test_update_rolling_summary_returns_false_when_pointer_not_promoted(monkeypatch):
    class _PointerRef:
        path = "lead_memories/lead-1/rolling_current/current"

    class _PointerCollection:
        def document(self, _doc_id: str):
            return _PointerRef()

    class _LeadDoc:
        def collection(self, _name: str):
            return _PointerCollection()

    class _RootCollection:
        def document(self, _doc_id: str):
            return _LeadDoc()

    class _Client:
        def collection(self, _name: str):
            return _RootCollection()

    monkeypatch.setattr(store, "_ensure_memory_root_document", lambda **_kwargs: None)
    monkeypatch.setattr(store, "require_client_for_write", lambda: _Client())
    monkeypatch.setattr(store, "create_rolling_artifact", lambda **_kwargs: True)
    monkeypatch.setattr(store, "promote_rolling_pointer", lambda **_kwargs: False)
    monkeypatch.setattr(store, "safe_execute", lambda fn, *args, **kwargs: None)

    written = store.update_rolling_summary(
        lead_id="lead-1",
        rolling_update={
            "rolling_summary_text": "fresh rolling",
            "open_questions": [],
            "carry_forward_notes": [],
            "days_count": 1,
            "last_daily_summary_date": "2026-01-01",
            "version": 1,
        },
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert written is False
