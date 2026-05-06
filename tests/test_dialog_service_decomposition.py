from __future__ import annotations

from types import SimpleNamespace

import pytest

from src.domain.models import ChatSession, Lead
from src.domain.pipeline_status import PipelineResult
from src.services.runtime.step_keys import StepKeys
from src.services.dialog.dialog_idempotency_wiring import build_send_reply_use_case
from src.services.dialog.dialog_orchestrator import DialogOrchestrator
from src.services.dialog.dialog_service import DialogService
from src.services.inbound.inbound_gate_service import InboundGateService


class _LeadRepo:
    def __init__(self) -> None:
        self.saved: list[Lead] = []
        self._lead = Lead(lead_id="canonical-42", stage=None, status=None)

    async def get_or_create_canonical(self, **_kwargs) -> Lead:
        return self._lead

    async def save(self, lead: Lead) -> None:
        self.saved.append(lead)


class _SessionRepo:
    async def get_or_create(self, **_kwargs) -> ChatSession:
        return ChatSession(id="telegram:42", channel="telegram", chat_id="42")


class _AllowLimiter:
    def __init__(self, allowed: bool = True) -> None:
        self.status = "allowed" if allowed else "denied_limit_exceeded"
        self.keys: list[str] = []

    def allow(self, key: str):
        self.keys.append(key)
        return SimpleNamespace(status=self.status)


class _InboundUseCase:
    def __init__(self) -> None:
        self.calls: list[tuple[dict, Lead, ChatSession]] = []

    async def execute(self, *, message: dict, lead: Lead, session: ChatSession) -> PipelineResult:
        self.calls.append((message, lead, session))
        return PipelineResult(status="ok", reply_text="ok")


class _Messaging:
    async def send_message(self, _chat_id, _text: str, **_kwargs) -> None:
        return None


class _IdentityResolution:
    async def resolve(self, *, channel: str, external_identity: str):
        return SimpleNamespace(
            canonical_lead_id="canonical-42",
        )


@pytest.mark.asyncio
async def test_inbound_gate_service_bootstraps_and_allows() -> None:
    gate = InboundGateService(
        leads_repo=_LeadRepo(),
        sessions_repo=_SessionRepo(),
        rate_limiter=_AllowLimiter(allowed=True),
        identity_resolution_service=_IdentityResolution(),
    )
    message = {"channel": "telegram", "chat_id": "42", "external_user_id": "42"}

    decision = await gate.prepare(message)

    assert decision.terminal_result is None
    assert decision.lead is not None
    assert decision.session is not None
    assert decision.lead.stage == "cold"
    assert decision.lead.status == "cold"


@pytest.mark.asyncio
async def test_inbound_gate_service_returns_rate_limited_terminal_result() -> None:
    gate = InboundGateService(
        leads_repo=_LeadRepo(),
        sessions_repo=_SessionRepo(),
        rate_limiter=_AllowLimiter(allowed=False),
        identity_resolution_service=_IdentityResolution(),
    )
    message = {"channel": "telegram", "chat_id": "42", "external_user_id": "42"}

    decision = await gate.prepare(message)

    assert decision.lead is None
    assert decision.session is None
    assert decision.terminal_result == PipelineResult(status="failed", error_type="rate_limited")


@pytest.mark.asyncio
async def test_dialog_orchestrator_delegates_to_use_case() -> None:
    use_case = _InboundUseCase()
    orchestrator = DialogOrchestrator(handle_inbound_message_use_case=use_case)
    lead = Lead(lead_id="telegram:42")
    session = ChatSession(id="telegram:42")
    message = {"text": "hello"}

    result = await orchestrator.execute(message=message, lead=lead, session=session)

    assert result.status == "ok"
    assert use_case.calls == [(message, lead, session)]


def test_dialog_idempotency_wiring_preserves_send_step_metadata_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    markers: list[tuple[str, dict | None]] = []
    checked: list[str] = []

    monkeypatch.setattr(
        "src.services.dialog.dialog_idempotency_wiring.StepIdempotencyPolicy.is_step_completed",
        lambda _self, *, step, context, channel=None, scope_override=None: checked.append(step) or False,
    )
    monkeypatch.setattr(
        "src.services.dialog.dialog_idempotency_wiring.StepIdempotencyPolicy.mark_step_completed",
        lambda _self, *, step, context, metadata=None, channel=None, scope_override=None: markers.append((step, metadata)) or True,
    )
    send_reply_use_case = build_send_reply_use_case(messaging=_Messaging())

    import asyncio

    asyncio.run(
        send_reply_use_case.execute(
            channel="telegram",
            chat_id="42",
            reply_text="hello",
            event_key="telegram:evt-1",
            owner_token="token-1",
        )
    )

    assert checked == [StepKeys.SEND_REPLY]
    assert markers[0] == (StepKeys.SEND_REPLY, {"channel": "telegram"})


@pytest.mark.asyncio
async def test_dialog_service_remains_compatible_thin_facade() -> None:
    service = DialogService(
        messaging=_Messaging(),
        leads_repo=_LeadRepo(),
        sessions_repo=_SessionRepo(),
        settings=SimpleNamespace(environment="test", rate_limit_backend="inmemory", rate_limit_max_events=10, rate_limit_window_seconds=60),
        rate_limiter=_AllowLimiter(),
        llm_service=SimpleNamespace(provider=object()),
    )
    service.inbound_gate_service = SimpleNamespace(
        prepare=lambda _msg: _async_result(
            SimpleNamespace(lead=Lead(lead_id="telegram:42"), session=ChatSession(id="telegram:42"), terminal_result=None)
        )
    )
    service.dialog_orchestrator = SimpleNamespace(
        execute=lambda **_kwargs: _async_result(PipelineResult(status="ok", reply_text="ok"))
    )

    result = await service.handle_normalized_message({"text": "hello"})

    assert result == PipelineResult(status="ok", reply_text="ok")


async def _async_result(value):
    return value
