import base64
import json
from datetime import datetime, timezone
from types import SimpleNamespace

from google.api_core.datetime_helpers import DatetimeWithNanoseconds
from fastapi.testclient import TestClient
import pytest

from src.domain.models import ChatSession, Lead
from src.domain.pipeline_status import PipelineResult
from src.services.rate_limit.contracts import RateLimitDecision
from src.main import app
from src.services.dialog.dialog_service import DialogService
from src.use_cases.dialog import GenerateReplyUseCase


def _test_safe_settings():
    return SimpleNamespace(
        environment="test",
        enable_distributed_rate_limit=False,
        rate_limit_backend="inmemory",
        rate_limit_max_events=100,
        rate_limit_window_seconds=60,
        rate_limit_fail_mode="closed",
        rate_limit_collection="runtime_rate_limits_test",
    )


class _FakeTelegram:
    async def send_message(self, _chat_id, _text: str, **_kwargs) -> None:
        return None


class _LeadRepo:
    async def get_or_create_canonical(self, **_kwargs):
        return Lead(lead_id="canonical-1", primary_channel="telegram", channel_user_id="1")

    async def save(self, _lead):
        return None

    async def update_last_activity(self, _lead_id, _now):
        return True

    async def append_message(self, **_kwargs):
        return True

    async def get(self, _lead_id):
        return Lead(lead_id="canonical-1", primary_channel="telegram", channel_user_id="1")

    async def apply_lead_patch(self, _lead_id, _patch):
        return True

    async def fetch_last_messages(self, **_kwargs):
        return []

    async def fetch_latest_daily_summary(self, **_kwargs):
        return None

    async def record_extraction_attempt(self, **_kwargs):
        return True


class _SessionRepo:
    async def get_or_create(self, **_kwargs):
        return ChatSession(id="telegram:1", channel="telegram", chat_id="1", external_user_id="1", lead_id="canonical-1")

    async def save(self, _session):
        return None

    async def get(self, _session_id):
        return ChatSession(id="telegram:1", channel="telegram", chat_id="1", external_user_id="1", lead_id="canonical-1")


def _pubsub_request_payload(data: dict) -> dict:
    encoded = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
    return {"message": {"data": encoded}}


def test_webhook_publish_failure_returns_non_200(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    # Inject mock rate limiters to always allow
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_rate_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_global_safety_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    response = client.post("/webhook/telegram", json={"update_id": 1, "message": {"message_id": 10, "date": 1710000000, "from": {"id": 1}, "chat": {"id": 1}, "text": "hi"}})

    assert response.status_code == 503
    assert response.json()["pipeline_status"] == "failed"


def test_webhook_publish_success_returns_200(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    # Inject mock rate limiters to always allow
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_rate_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_global_safety_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: "id")

    response = client.post("/webhook/telegram", json={"update_id": 1, "message": {"message_id": 10, "date": 1710000000, "from": {"id": 1}, "chat": {"id": 1}, "text": "hi"}})

    assert response.status_code == 200
    assert response.json()["pipeline_status"] == "success"




def test_webhook_retry_after_publish_failure_is_retried(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    attempts = {"count": 0}

    def _publish(*_args, **_kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")
        return "id"

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", _publish)

    payload = {"update_id": 99, "message": {"message_id": 90, "date": 1710000000, "from": {"id": 1}, "chat": {"id": 1}, "text": "hi"}}

    first = client.post("/webhook/telegram", json=payload)
    second = client.post("/webhook/telegram", json=payload)

    assert first.status_code == 503
    assert first.json()["status"] == "enqueue_failed"
    assert second.status_code == 200
    assert second.json()["status"] == "queued"
    assert attempts["count"] == 2


def test_pubsub_success_marks_completed(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "src.entrypoints.pubsub_pipeline.start_normalized_event_processing",
        lambda **_kwargs: type("S", (), {"decision": "started", "should_process": True, "status": "processing"})(),
    )
    completed = {"called": False}
    monkeypatch.setattr("src.entrypoints.pubsub_pipeline.complete_normalized_event_processing", lambda *_args, **_kwargs: completed.__setitem__("called", True))
    monkeypatch.setattr("src.entrypoints.pubsub_pipeline.fail_normalized_event_processing", lambda *_args, **_kwargs: None)

    class _Svc:
        async def handle_normalized_message(self, _normalized):
            return PipelineResult(status="success", reply_text="ok")

    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: _Svc())

    response = client.post("/pubsub", json=_pubsub_request_payload({"channel": "telegram", "source_identity": "1", "event_identity": "1", "conversation_identity": "1", "text": "hi"}))

    assert response.status_code == 200
    assert completed["called"] is True


def test_pubsub_dialog_error_marks_failed(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "src.entrypoints.pubsub_pipeline.start_normalized_event_processing",
        lambda **_kwargs: type("S", (), {"decision": "started", "should_process": True, "status": "processing"})(),
    )
    failed = {"called": False}
    monkeypatch.setattr("src.entrypoints.pubsub_pipeline.complete_normalized_event_processing", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("src.entrypoints.pubsub_pipeline.fail_normalized_event_processing", lambda *_args, **_kwargs: failed.__setitem__("called", True))

    class _Svc:
        async def handle_normalized_message(self, _normalized):
            raise RuntimeError("dialog")

    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: _Svc())

    response = client.post("/pubsub", json=_pubsub_request_payload({"channel": "telegram", "source_identity": "1", "event_identity": "1", "conversation_identity": "1", "text": "hi"}))

    assert response.status_code == 500
    assert failed["called"] is True


def test_pubsub_completed_duplicate_skipped(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "src.entrypoints.pubsub_pipeline.start_normalized_event_processing",
        lambda **_kwargs: type(
            "S",
            (),
            {"decision": "already_completed", "should_process": False, "status": "completed"},
        )(),
    )

    response = client.post("/pubsub", json=_pubsub_request_payload({"channel": "telegram", "source_identity": "1", "event_identity": "1", "conversation_identity": "1", "text": "hi"}))

    assert response.status_code == 200
    assert response.json()["status"] == "duplicate_skipped"


def test_pubsub_failed_retry_reprocessed(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(
        "src.entrypoints.pubsub_pipeline.start_normalized_event_processing",
        lambda **_kwargs: type("S", (), {"decision": "started", "should_process": True, "status": "processing"})(),
    )
    monkeypatch.setattr("src.entrypoints.pubsub_pipeline.complete_normalized_event_processing", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("src.entrypoints.pubsub_pipeline.fail_normalized_event_processing", lambda *_args, **_kwargs: None)

    class _Svc:
        async def handle_normalized_message(self, _normalized):
            return PipelineResult(status="degraded", reply_text="fallback")

    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: _Svc())

    response = client.post("/pubsub", json=_pubsub_request_payload({"channel": "telegram", "source_identity": "1", "event_identity": "1", "conversation_identity": "1", "text": "hi"}))

    assert response.status_code == 200
    assert response.json()["pipeline_status"] == "degraded"


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


def test_llm_fallback_is_degraded_not_success(monkeypatch):
    class _LLM:
        provider = type("P", (), {"provider_name": "fake"})()

        async def run(self, *_args, **_kwargs):
            from src.llm.llm_base_contracts import LLMResult

            return LLMResult(
                task="primary_agent_reply_task",
                ok=False,
                data={"reply_text": "fallback", "system_payload": None},
                error={"kind": "provider_error", "message": "x"},
            )

    class _AllowLimiter:
        def allow(self, key: str) -> RateLimitDecision:
            return RateLimitDecision(status="allowed")

    service = DialogService(
        _FakeTelegram(),
        leads_repo=_LeadRepo(),
        sessions_repo=_SessionRepo(),
        settings=_test_safe_settings(),
        rate_limiter=_AllowLimiter(), # Inject the mock rate limiter
        llm_service=_LLM(),
    )

    result = __import__("asyncio").run(
        service.handle_normalized_message(
            {
                "channel": "telegram",
                "conversation_identity": "1",
                "source_identity": "1",
                "event_identity": "evt-2",
                "text": "hi",
            }
        )
    )

    assert result.reply_text == "fallback"
    assert result.status == "degraded"


def test_generate_reply_use_case_serializes_nested_firestore_timestamps():
    captured_payload = {}

    class _LLM:
        async def run(self, *, task, payload, meta):
            from src.llm.llm_base_contracts import LLMResult

            captured_payload["task"] = task
            captured_payload["payload"] = payload
            captured_payload["meta"] = meta
            return LLMResult(task="primary_agent_reply_task", ok=True, data={"reply_text": "ok", "system_payload": None})

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
                task="primary_agent_reply_task",
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
