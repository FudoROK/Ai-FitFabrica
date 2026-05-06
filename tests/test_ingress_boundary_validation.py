import base64
import json
from datetime import date

from fastapi.testclient import TestClient
import pytest

from src.entrypoints.payloads import PubSubPushRequest, decode_pubsub_payload
from src.main import app
from src.memory_layer.services.memory_summary_service import MemorySummaryResult
from src.services import pubsub_service
from src.services.rate_limit import RateLimitDecision


client = TestClient(app)


def _pubsub_request_payload(data: dict) -> dict:
    encoded = base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
    return {"message": {"data": encoded}}


def _normalized_text_payload() -> dict:
    return {
        "channel": "telegram",
        "source_identity": "2",
        "event_identity": "1",
        "conversation_identity": "1",
        "external_user_id": "2",
        "text": "hello",
        "timestamp": "2026-03-20T00:00:00+00:00",
        "content_type": "text",
    }


def _normalized_voice_payload() -> dict:
    return {
        "channel": "telegram",
        "source_identity": "2",
        "event_identity": "2",
        "conversation_identity": "1",
        "external_user_id": "2",
        "text": "[voice]",
        "timestamp": "2026-03-20T00:00:01+00:00",
        "content_type": "voice",
        "media": {
            "file_id": "voice-file",
            "duration": 3,
            "mime_type": "audio/ogg",
            "file_size": 12345,
        },
    }


def _normalized_photo_payload() -> dict:
    return {
        "channel": "telegram",
        "source_identity": "2",
        "event_identity": "3",
        "conversation_identity": "1",
        "external_user_id": "2",
        "text": "[photo]",
        "timestamp": "2026-03-20T00:00:02+00:00",
        "content_type": "photo",
        "media": {
            "sizes": [
                {"file_id": "small-photo"},
                {"file_id": "big-photo"},
            ]
        },
    }


def _normalized_document_payload() -> dict:
    return {
        "channel": "telegram",
        "source_identity": "2",
        "event_identity": "4",
        "conversation_identity": "1",
        "external_user_id": "2",
        "text": "contract.pdf",
        "timestamp": "2026-03-20T00:00:03+00:00",
        "content_type": "document",
        "media": {
            "file_id": "doc-file",
            "file_name": "contract.pdf",
            "mime_type": "application/pdf",
            "file_size": 321,
        },
    }


def test_telegram_realistic_text_update_with_extra_nested_fields_passes(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    captured = {"normalized": None}

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: "ok")

    def _normalize(update):
        captured["normalized"] = update
        from src.domain.normalized_ingress_event import NormalizedIngressEvent

        return NormalizedIngressEvent(
            channel="telegram",
            source_identity="2",
            conversation_identity="1",
            external_user_id="2",
            text="hello",
            event_identity=99,
        )

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.normalize_telegram_update", _normalize)

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 99,
            "message": {
                "message_id": 777,
                "date": 1710000000,
                "from": {"id": 2, "first_name": "John", "is_bot": False, "language_code": "en"},
                "chat": {"id": 1, "type": "private", "first_name": "John"},
                "text": "hello",
                "entities": [{"offset": 0, "length": 5, "type": "bold"}],
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "queued"
    assert captured["normalized"] is not None


def test_telegram_voice_update_passes_boundary(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: "ok")

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 100,
            "message": {
                "message_id": 778,
                "date": 1710000001,
                "from": {"id": 2, "first_name": "John"},
                "chat": {"id": 1, "type": "private"},
                "voice": {"file_id": "voice-file", "duration": 3, "mime_type": "audio/ogg", "file_size": 12345, "extra": True},
            },
        },
    )

    assert response.status_code == 200


def test_telegram_photo_update_passes_boundary(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: "ok")

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 101,
            "message": {
                "message_id": 779,
                "date": 1710000002,
                "from": {"id": 2},
                "chat": {"id": 1},
                "caption": "photo caption",
                "photo": [
                    {"file_id": "small-photo", "file_size": 1000},
                    {"file_id": "big-photo", "width": 1000, "height": 1000},
                ],
            },
        },
    )

    assert response.status_code == 200


def test_telegram_document_update_passes_boundary(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: "ok")

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 102,
            "message": {
                "message_id": 780,
                "date": 1710000003,
                "from": {"id": 2},
                "chat": {"id": 1},
                "document": {
                    "file_id": "doc-file",
                    "file_name": "contract.pdf",
                    "mime_type": "application/pdf",
                    "file_size": 321,
                    "thumb": {"file_id": "thumb"},
                },
            },
        },
    )

    assert response.status_code == 200


def test_telegram_extra_nested_fields_do_not_fail(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: "ok")

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 103,
            "message": {
                "message_id": 781,
                "date": 1710000004,
                "from": {"id": 2, "foo": "bar", "nested": {"x": 1}},
                "chat": {"id": 1, "type": "private", "another": [1, 2, 3]},
                "text": "ok",
                "random_new_telegram_field": {"k": "v"},
            },
        },
    )

    assert response.status_code == 200


def test_telegram_missing_required_field_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    response = client.post("/webhook/telegram", json={"message": {"chat": {"id": 1}, "from": {"id": 1}}})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_telegram_payload"


def test_telegram_truly_malformed_payload_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    response = client.post("/webhook/telegram", content="{", headers={"content-type": "application/json"})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_telegram_payload"


def test_telegram_unsupported_valid_update_kind_is_ignored(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 123,
            "callback_query": {"id": "abc", "from": {"id": 1}, "chat_instance": "ci", "data": "click"},
        },
    )

    assert response.status_code == 200
    assert response.json()["reason"] == "unsupported_update_kind"


def test_telegram_oversized_payload_rejected_before_runtime(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    called = {"normalize": False}

    def _normalize(_payload):
        called["normalize"] = True
        return {}

    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.normalize_telegram_update", _normalize)

    response = client.post(
        "/webhook/telegram",
        json={
            "update_id": 1,
            "message": {
                "message_id": 900,
                "date": 1710009999,
                "chat": {"id": 1},
                "from": {"id": 1},
                "text": "x" * 300_000,
            },
        },
    )

    assert response.status_code == 413
    assert called["normalize"] is False


def test_ingress_antiflood_rejects_single_source_before_publish(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)

    publish_calls = {"count": 0}

    def _publish(*_args, **_kwargs):
        publish_calls["count"] += 1
        return "ok"

    class _SingleSourceLimiter:
        def __init__(self):
            self._seen = 0

        def allow(self, _key: str) -> RateLimitDecision:
            self._seen += 1
            if self._seen > 1:
                return RateLimitDecision(status="denied_limit_exceeded", remaining=0, retry_after_seconds=15, reason="rate_limit_exceeded")
            return RateLimitDecision(status="allowed", remaining=0)
    source_limiter = _SingleSourceLimiter()
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", _publish)
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.ingress_rate_limiter", lambda _settings: source_limiter)
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_global_safety_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )

    payload = {
        "update_id": 301,
        "message": {"message_id": 1, "date": 1710000000, "from": {"id": 2}, "chat": {"id": 1}, "text": "hello"},
    }
    first = client.post("/webhook/telegram", json=payload)
    second = client.post("/webhook/telegram", json={**payload, "update_id": 302, "message": {**payload["message"], "message_id": 2}})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.json()["reason"] == "ingress_source_rate_limit_exceeded"
    assert publish_calls["count"] == 1


def test_ingress_antiflood_does_not_merge_distinct_sources(monkeypatch):
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.has_valid_token", lambda *_args, **_kwargs: True)
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.publish_normalized_update", lambda *_args, **_kwargs: "ok")
    monkeypatch.setattr(
        "src.entrypoints.telegram_webhook_routes.ingress_global_safety_limiter",
        lambda _settings: type("AllowAll", (), {"allow": lambda *_args, **_kwargs: RateLimitDecision(status="allowed")})(),
    )

    class _PerKeyLimiter:
        def __init__(self):
            self._counts: dict[str, int] = {}

        def allow(self, key: str) -> RateLimitDecision:
            new_count = self._counts.get(key, 0) + 1
            self._counts[key] = new_count
            return RateLimitDecision(status="allowed" if new_count <= 1 else "denied_limit_exceeded", remaining=max(1 - new_count, 0), reason="rate_limit_exceeded")

    per_key_limiter = _PerKeyLimiter()
    monkeypatch.setattr("src.entrypoints.telegram_webhook_routes.ingress_rate_limiter", lambda _settings: per_key_limiter)

    first_user = client.post(
        "/webhook/telegram",
        json={"update_id": 401, "message": {"message_id": 1, "date": 1710000000, "from": {"id": 11}, "chat": {"id": 101}, "text": "u1"}},
    )
    second_user = client.post(
        "/webhook/telegram",
        json={"update_id": 402, "message": {"message_id": 2, "date": 1710000001, "from": {"id": 22}, "chat": {"id": 202}, "text": "u2"}},
    )

    assert first_user.status_code == 200
    assert second_user.status_code == 200


def test_ingress_rate_key_is_channel_aware():
    from src.domain.normalized_ingress_event import NormalizedIngressEvent, build_ingress_rate_key

    telegram_key = build_ingress_rate_key(
        NormalizedIngressEvent(channel="telegram", source_identity="42", event_identity="1", conversation_identity="1")
    )
    whatsapp_key = build_ingress_rate_key(
        NormalizedIngressEvent(channel="whatsapp", source_identity="42", event_identity="1", conversation_identity="1")
    )

    assert telegram_key == "telegram:42"
    assert whatsapp_key == "whatsapp:42"
    assert telegram_key != whatsapp_key


def test_normalized_ingress_contract_requires_source_identity():
    from pydantic import ValidationError

    from src.domain.normalized_ingress_event import NormalizedIngressEvent

    with pytest.raises(ValidationError):
        NormalizedIngressEvent(channel="telegram", event_identity="1", conversation_identity="1")


def test_telegram_normalizer_populates_required_source_identity():
    from src.adapters.messaging.telegram.telegram_handler import normalize_telegram_update
    from src.entrypoints.payloads import TelegramWebhookRequest

    update = TelegramWebhookRequest.model_validate(
        {
            "update_id": 777,
            "message": {
                "message_id": 12,
                "date": 1710000000,
                "from": {"id": 987},
                "chat": {"id": 654},
                "text": "hello",
            },
        }
    )

    normalized = normalize_telegram_update(update)

    assert normalized.source_identity == "987"
    assert normalized.channel == "telegram"


def test_policy_layer_no_longer_owns_source_identity_guessing():
    import src.entrypoints.policies as policies

    assert not hasattr(policies, "extract_ingress_source_identity")
    assert not hasattr(policies, "build_ingress_rate_key")


def test_pubsub_missing_required_fields_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    response = client.post("/pubsub", json={"message": {}})

    assert response.status_code == 400


def test_pubsub_outer_envelope_accepts_top_level_delivery_attempt(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    payload = _pubsub_request_payload(_normalized_text_payload())
    payload["deliveryAttempt"] = 2

    response = client.post("/pubsub", json=payload)

    assert response.status_code == 200


def test_pubsub_outer_envelope_accepts_message_ordering_key(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    payload = _pubsub_request_payload(_normalized_text_payload())
    payload["message"]["orderingKey"] = "lead-1"

    response = client.post("/pubsub", json=payload)

    assert response.status_code == 200


def test_pubsub_outer_envelope_accepts_delivery_attempt_and_ordering_key(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    payload = _pubsub_request_payload(_normalized_text_payload())
    payload["deliveryAttempt"] = 3
    payload["message"]["orderingKey"] = "lead-2"

    response = client.post("/pubsub", json=payload)

    assert response.status_code == 200


def test_pubsub_missing_message_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    response = client.post("/pubsub", json={"subscription": "projects/x/subscriptions/y"})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_pubsub_message"


def test_pubsub_missing_message_data_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    response = client.post("/pubsub", json={"message": {"messageId": "1"}})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_pubsub_message"


def test_pubsub_non_string_message_data_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    response = client.post("/pubsub", json={"message": {"data": 123}})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_pubsub_message"


def test_pubsub_malformed_nested_schema_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    response = client.post("/pubsub", json={"message": {"data": base64.b64encode(b'{"channel": "telegram", "conversation_identity": "1"}').decode("utf-8")}})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_pubsub_message"


def test_pubsub_invalid_base64_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    response = client.post("/pubsub", json={"message": {"data": "%%%not-base64%%%"}})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_pubsub_message"


def test_pubsub_invalid_json_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)
    encoded = base64.b64encode(b'{"channel": ').decode("utf-8")

    response = client.post("/pubsub", json={"message": {"data": encoded}})

    assert response.status_code == 400
    assert response.json()["error"] == "invalid_pubsub_message"


def test_pubsub_wrong_type_in_decoded_payload_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    response = client.post(
        "/pubsub",
        json=_pubsub_request_payload({"channel": ["telegram"], "event_identity": "1", "conversation_identity": "1"}),
    )

    assert response.status_code == 400


def test_pubsub_oversized_payload_rejected_before_runtime(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    called = {"process": False}

    async def _process(**_kwargs):
        called["process"] = True

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)

    response = client.post(
        "/pubsub",
        json={"message": {"data": "A" * 300_000}},
    )

    assert response.status_code == 413
    assert called["process"] is False


def test_pubsub_text_normalized_payload_passes(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    response = client.post("/pubsub", json=_pubsub_request_payload(_normalized_text_payload()))

    assert response.status_code == 200


def test_pubsub_voice_normalized_payload_passes(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    response = client.post("/pubsub", json=_pubsub_request_payload(_normalized_voice_payload()))

    assert response.status_code == 200


def test_pubsub_photo_normalized_payload_passes(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    response = client.post("/pubsub", json=_pubsub_request_payload(_normalized_photo_payload()))

    assert response.status_code == 200


def test_pubsub_document_normalized_payload_passes(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    response = client.post("/pubsub", json=_pubsub_request_payload(_normalized_document_payload()))

    assert response.status_code == 200


def test_memory_summary_malformed_request_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.internal_task_routes.verify_internal_oidc_bearer", lambda *_args, **_kwargs: True)

    response = client.post("/tasks/memory-summary", content="not-json", headers={"content-type": "application/json"})

    assert response.status_code == 400


def test_memory_summary_empty_body_runs_batch_mode(monkeypatch):
    monkeypatch.setattr("src.entrypoints.internal_task_routes.verify_internal_oidc_bearer", lambda *_args, **_kwargs: True)
    called = {"lead_id": "not-set"}

    class _Svc:
        async def build_memory_summary_for_lead(self, **kwargs):
            called["lead_id"] = kwargs.get("lead_id")
            return MemorySummaryResult(
                date=date(2026, 3, 19),
                leads_processed=3,
                summaries_written=2,
                errors=["summary_error"],
                failed_leads=[{"lead_id": "lead-3", "reason": "summary_error"}],
                total_selected=5,
            )

    monkeypatch.setattr("src.entrypoints.internal_task_routes.memory_summary_service", lambda _settings=None: _Svc())

    response = client.post("/tasks/memory-summary", json={})

    assert response.status_code == 200
    assert called["lead_id"] is None
    assert response.json() == {
        "pipeline_status": "completed",
        "mode": "batch",
        "total_selected": 5,
        "total_processed": 3,
        "total_succeeded": 0,
        "total_failed": 0,
        "failed": [{"lead_id": "lead-3", "reason": "summary_error"}],
        "outcomes": {
            "success": 0,
            "rejected": 0,
            "skipped": 0,
            "idempotent_noop": 0,
            "failed": 0,
        },
        "reason_codes": {},
    }


def test_memory_summary_wrong_type_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.internal_task_routes.verify_internal_oidc_bearer", lambda *_args, **_kwargs: True)

    response = client.post("/tasks/memory-summary", json={"lead_id": 42})

    assert response.status_code == 400


def test_memory_summary_oversized_rejected(monkeypatch):
    monkeypatch.setattr("src.entrypoints.internal_task_routes.verify_internal_oidc_bearer", lambda *_args, **_kwargs: True)

    response = client.post("/tasks/memory-summary", json={"lead_id": "x" * 300_000})

    assert response.status_code == 413







def test_memory_summary_task_related_handler_uses_same_sanitized_contract(monkeypatch):
    monkeypatch.setattr("src.entrypoints.internal_task_routes.verify_internal_oidc_bearer", lambda *_args, **_kwargs: True)

    class _Svc:
        async def build_memory_summary_for_lead(self, **_kwargs):
            return MemorySummaryResult(
                date=date(2026, 3, 19),
                leads_processed=1,
                summaries_written=0,
                errors=["hubspot sync failed for telegram:42"],
            )

    monkeypatch.setattr("src.entrypoints.internal_task_routes.memory_summary_service", lambda _settings=None: _Svc())

    response = client.post("/tasks/memory-summary", json={"lead_id": "lead-1"})

    assert response.status_code == 200
    assert response.json() == {
        "pipeline_status": "completed",
        "date": "2026-03-19",
        "leads_processed": 1,
        "summaries_written": 0,
        "error_count": 1,
        "has_errors": True,
        "outcomes": {
            "success": 0,
            "rejected": 0,
            "skipped": 0,
            "idempotent_noop": 0,
            "failed": 0,
        },
        "reason_codes": {},
    }
    assert "errors" not in response.json()
    assert "lead_id" not in response.json()


def test_valid_payload_still_reaches_runtime(monkeypatch):
    monkeypatch.setattr("src.entrypoints.pubsub_routes.verify_pubsub_oidc_jwt", lambda *_args, **_kwargs: True)

    called = {"process": False}

    class _Outcome:
        kind = "ok"
        pipeline_status = "success"

    async def _process(**_kwargs):
        called["process"] = True
        return _Outcome()

    monkeypatch.setattr("src.entrypoints.pubsub_routes.process_pubsub_normalized_event", _process)
    monkeypatch.setattr("src.entrypoints.pubsub_routes.dialog_service", lambda _settings=None: type("S", (), {"handle_normalized_message": None})())

    response = client.post(
        "/pubsub",
        json=_pubsub_request_payload({"channel": "telegram", "source_identity": "2", "event_identity": "1", "conversation_identity": "1", "text": "hi"}),
    )

    assert response.status_code == 200
    assert called["process"] is True


def test_publish_and_ingest_contract_alignment_roundtrip(monkeypatch):
    published = {"raw_data": None}

    class _Future:
        def result(self):
            return "pubsub-message-id"

    class _Publisher:
        @staticmethod
        def topic_path(project: str, topic: str) -> str:
            return f"projects/{project}/topics/{topic}"

        def publish(self, _topic_path: str, *, data: bytes, source: str):
            assert source == "telegram-webhook"
            published["raw_data"] = data
            return _Future()

    monkeypatch.setattr(pubsub_service, "_publisher", lambda: _Publisher())
    monkeypatch.setattr(
        pubsub_service,
        "load_settings",
        lambda: type("Settings", (), {"pubsub_topic_name": "topic", "gcp_project_id": "project"})(),
    )

    payload = _normalized_voice_payload()
    message_id = pubsub_service.publish_normalized_update(payload)
    assert message_id == "pubsub-message-id"

    envelope = {
        "message": {"data": base64.b64encode(published["raw_data"]).decode("utf-8"), "orderingKey": "lead-voice"},
        "subscription": "projects/project/subscriptions/sub",
        "deliveryAttempt": 1,
    }
    decoded = decode_pubsub_payload(PubSubPushRequest.model_validate(envelope))

    assert decoded["content_type"] == "voice"
    assert decoded["media"]["file_id"] == "voice-file"
