from __future__ import annotations

import pytest

from src.services.runtime.step_keys import StepKeys
from src.use_cases.dialog.send_reply_use_case import SendReplyUseCase


class _Messaging:
    def __init__(self) -> None:
        self.calls: list[tuple[str | int, str]] = []

    async def send_message(self, chat_id, text: str, **_kwargs):
        self.calls.append((chat_id, text))


class _PolicySpy:
    def __init__(self) -> None:
        self.checked: list[tuple[str, str, str | None]] = []
        self.marked: list[tuple[str, str, str | None, dict]] = []

    def resolve_step_key(self, *, step: str, channel: str | None = None) -> str:
        return f"{channel}_send_reply" if step == StepKeys.SEND_REPLY else step

    def is_step_completed(self, *, step: str, context, channel: str | None = None, scope_override: str | None = None) -> bool:
        self.checked.append((step, channel or "", context.event_key))
        return False

    def mark_step_completed(self, *, step: str, context, metadata=None, channel: str | None = None, scope_override: str | None = None) -> bool:
        self.marked.append((step, channel or "", context.event_key, metadata or {}))
        return True


def test_send_reply_use_case_has_no_legacy_compat_methods():
    assert not hasattr(SendReplyUseCase, "is_step_completed")
    assert not hasattr(SendReplyUseCase, "mark_step_completed")


@pytest.mark.asyncio
async def test_send_reply_use_case_is_channel_agnostic():
    messaging = _Messaging()
    policy = _PolicySpy()
    use_case = SendReplyUseCase(
        messaging=messaging,
        step_idempotency=policy,
    )

    sent = await use_case.execute(
        channel="whatsapp",
        chat_id="wa-chat-99",
        reply_text="hello",
        event_key="evt-1",
        owner_token="tok-1",
    )

    assert sent is True
    assert messaging.calls == [("wa-chat-99", "hello")]
    assert policy.checked == [(StepKeys.SEND_REPLY, "whatsapp", "evt-1")]
    assert policy.marked == [(StepKeys.SEND_REPLY, "whatsapp", "evt-1", {"channel": "whatsapp"})]
