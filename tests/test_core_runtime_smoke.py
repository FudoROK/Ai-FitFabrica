import json
from datetime import datetime, timezone

from google.api_core.datetime_helpers import DatetimeWithNanoseconds
import pytest

from src.use_cases.dialog import GenerateReplyUseCase

def test_firestore_write_error_is_not_silent(monkeypatch):
    import src.adapters.database.firestore.storage_primitives as sp
    import src.adapters.database.firestore.lead_store as lead_store

    class _Snapshot:
        exists = True

        def to_dict(self):
            return {}

    class _Doc:
        def get(self):
            return _Snapshot()

        def set(self, *_args, **_kwargs):
            raise RuntimeError("firestore write failed")

    class _Collection:
        def document(self, *_args, **_kwargs):
            return _Doc()

    class _Client:
        def collection(self, *_args, **_kwargs):
            return _Collection()

    monkeypatch.setattr(lead_store, "require_client_for_write", lambda: _Client())

    with pytest.raises(RuntimeError, match="firestore write failed"):
        sp.apply_lead_patch("telegram:1", {"first_name": "A"})


def test_generate_reply_use_case_serializes_nested_firestore_timestamps():
    captured_payload = {}

    class _LLM:
        async def run(self, *, task, payload, meta):
            from src.llm.llm_base_contracts import LLMResult

            captured_payload["task"] = task
            captured_payload["payload"] = payload
            captured_payload["meta"] = meta
            return LLMResult(task="dialog_reply_task", ok=True, data={"reply_text": "ok", "system_payload": None})

    use_case = GenerateReplyUseCase(_LLM())

    firestore_ts = DatetimeWithNanoseconds(2025, 1, 2, 3, 4, 5, 123456, tzinfo=timezone.utc)
    llm_context = {
        "created_at": firestore_ts,
        "nested": {
            "items": [datetime(2025, 1, 2, 3, 4, 6, tzinfo=timezone.utc), (firestore_ts,)],
        },
    }

    result, reply_text, system_payload, reply_meta = __import__("asyncio").run(
        use_case.execute(
            message={"message_id": 42},
            channel="telegram",
            lead_id="canonical-1",
            text="hi",
            llm_context=llm_context,
        )
    )

    assert result.ok is True
    assert reply_text == "ok"
    assert system_payload is None
    assert reply_meta == {}

    payload = captured_payload["payload"]
    assert payload["context"]["created_at"] == firestore_ts.isoformat()
    assert payload["context"]["nested"]["items"][0] == "2025-01-02T03:04:06+00:00"
    assert payload["context"]["nested"]["items"][1][0] == firestore_ts.isoformat()
    assert payload["runtime_envelope"]["request_type"] == "primary_dialog_turn"
    assert payload["runtime_envelope"]["contract_version"] == "primary_runtime_envelope_v1"
    assert payload["runtime_envelope"]["backend_context"] == payload["context"]

    parsed_input = json.loads(payload["input"])
    assert parsed_input["request_type"] == "primary_dialog_turn"
    assert parsed_input["contract_version"] == "primary_runtime_envelope_v1"
    assert parsed_input["user_text"] == "hi"
    assert parsed_input["backend_context"] == payload["context"]


def test_generate_reply_use_case_exposes_normalized_provider_session_id():
    class _LLM:
        async def run(self, *, task, payload, meta):
            from src.llm.llm_base_contracts import LLMResult

            return LLMResult(
                task="dialog_reply_task",
                ok=True,
                data={
                    "reply_text": "ok",
                    "system_payload": None,
                },
                provider_metadata={"vertex_session_id": "session-123"},
            )

    use_case = GenerateReplyUseCase(_LLM())

    _result, _reply_text, _system_payload, reply_meta = __import__("asyncio").run(
        use_case.execute(
            message={"message_id": 42},
            channel="telegram",
            lead_id="canonical-1",
            text="hi",
            llm_context={},
        )
    )

    assert reply_meta == {"provider_session_id": "session-123"}
