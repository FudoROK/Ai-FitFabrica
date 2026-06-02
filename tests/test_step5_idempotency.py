from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.adapters.database.firestore import storage_primitives as sp
from src.use_cases.dialog.handle_inbound_message_use_case import HandleInboundMessageUseCase
from src.use_cases.dialog.send_reply_use_case import SendReplyUseCase
from src.domain.models import ChatSession, Lead


class _DocRef:
    def __init__(self, storage: dict[str, dict], doc_id: str):
        self.storage = storage
        self.doc_id = doc_id

    def set(self, payload, merge=False):
        if merge and self.doc_id in self.storage:
            current = dict(self.storage[self.doc_id])
            current.update(payload)
            self.storage[self.doc_id] = current
            return
        self.storage[self.doc_id] = dict(payload)


class _Collection:
    def __init__(self, storage: dict[str, dict]):
        self.storage = storage
        self.auto_counter = 0

    def document(self, doc_id=None):
        if doc_id is None:
            self.auto_counter += 1
            doc_id = f"auto-{self.auto_counter}"
        return _DocRef(self.storage, str(doc_id))


class _Client:
    def __init__(self):
        self.storage: dict[str, dict] = {}

    def collection(self, _name: str):
        return _Collection(self.storage)


class _Messaging:
    def __init__(self):
        self.calls: list[tuple[str | int | None, str]] = []

    async def send_message(self, chat_id, text: str, **_kwargs):
        self.calls.append((chat_id, text))


async def _build_context(**_kwargs):
    return {"session": {}}


class _GenerateReply:
    async def execute(self, **_kwargs):
        return (
            type("LLMResult", (), {"ok": True, "error": {}})(),
            "dialog_reply_task",
            {},
            {},
        )


class _PersistConversation:
    def __init__(self):
        self.message_keys: list[str | None] = []

    async def execute(self, **kwargs):
        event_key = kwargs.get("event_key")
        if event_key:
            self.message_keys.extend([f"{event_key}:message:user", f"{event_key}:message:assistant"])


class _NoopWorkflowProcessor:
    async def execute(self, **_kwargs):
        return False


def test_firestore_message_append_uses_deterministic_key_for_retry(monkeypatch):
    import src.adapters.database.firestore.message_store as message_store

    client = _Client()
    monkeypatch.setattr(message_store, "require_client_for_write", lambda: client)

    now = datetime.now(timezone.utc)
    first = sp.append_message_with_ttl(
        lead_id="telegram:1",
        role="assistant",
        text="hello",
        timestamp=now,
        message_idempotency_key="telegram:evt-1:message:assistant",
    )
    second = sp.append_message_with_ttl(
        lead_id="telegram:1",
        role="assistant",
        text="hello",
        timestamp=now,
        message_idempotency_key="telegram:evt-1:message:assistant",
    )

    assert first is True
    assert second is True
    assert len(client.storage) == 1


@pytest.mark.asyncio
async def test_telegram_send_is_idempotent_across_retries():
    completed_steps: set[str] = set()

    class _Policy:
        def resolve_step_key(self, *, step: str, channel: str | None = None) -> str:
            return f"{channel}_send_reply"

        def is_step_completed(self, *, step: str, context, channel: str | None = None, scope_override: str | None = None):
            _ = step
            _ = scope_override
            return f"{context.event_key}:{channel}_send_reply" in completed_steps

        def mark_step_completed(self, *, step: str, context, metadata=None, channel: str | None = None, scope_override: str | None = None):
            _ = step
            _ = metadata
            _ = scope_override
            completed_steps.add(f"{context.event_key}:{channel}_send_reply")
            return True

    messaging = _Messaging()
    persist = _PersistConversation()
    send_reply_use_case = SendReplyUseCase(
        messaging=messaging,
        step_idempotency=_Policy(),
    )

    use_case = HandleInboundMessageUseCase(
        leads_repo=object(),
        llm_service=type("LLM", (), {"provider": object()})(),
        build_context=_build_context,
        generate_reply_use_case=_GenerateReply(),
        persist_conversation_use_case=persist,
        send_reply_use_case=send_reply_use_case,
        process_lead_workflow_output_use_case=_NoopWorkflowProcessor(),
    )

    lead = Lead(lead_id="telegram:1")
    session = ChatSession(id="telegram:1")
    message = {
        "channel": "telegram",
        "conversation_identity": "1",
        "source_identity": "1",
        "text": "hi",
        "_event_key": "telegram:evt-1",
        "_processing_token": "token-1",
    }

    await use_case.execute(message=message, lead=lead, session=session)
    await use_case.execute(message=message, lead=lead, session=session)

    assert messaging.calls == [("1", "dialog_reply_task")]
    assert "telegram:evt-1:message:user" in persist.message_keys
    assert "telegram:evt-1:message:assistant" in persist.message_keys
