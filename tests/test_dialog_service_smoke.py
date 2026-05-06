import asyncio
from types import SimpleNamespace

from src.domain.models import ChatSession, Lead
from src.domain.pipeline_status import PipelineResult
from src.services.rate_limit.contracts import RateLimitDecision
from src.services.dialog.dialog_service import DialogService


def _test_safe_settings():
    return SimpleNamespace(
        environment="test",
        enable_distributed_rate_limit=False,
        rate_limit_backend="inmemory",
        rate_limit_max_events=100,
        rate_limit_window_seconds=60,
        rate_limit_fail_mode="closed",
        rate_limit_collection="runtime_rate_limits_test",
        enable_profile_runtime=False,
    )


class FakeTelegramClient:
    def __init__(self) -> None:
        self.sent_messages: list[tuple[str | int, str]] = []

    async def send_message(self, chat_id, text: str, **_kwargs) -> None:
        self.sent_messages.append((chat_id, text))


class InMemoryLeadRepository:
    def __init__(self) -> None:
        self._lead: Lead | None = None
        self.leads: dict[str, dict] = {}
        self.messages: dict[str, list[dict]] = {}
        self.daily_summaries: dict[str, dict] = {}
        self.extraction_attempts: dict[str, list[dict]] = {}

    class LeadRecord(dict):
        def __getattr__(self, item):  # noqa: ANN001 - minimal test helper
            return self.get(item)

    async def get_or_create_canonical(
        self,
        *,
        canonical_lead_id: str,
        channel: str,
        external_user_id: str | int | None,
        username: str | None,
        first_name: str | None,
    ) -> Lead:
        if self._lead:
            return self._lead
        self._lead = Lead(
            lead_id=canonical_lead_id,
            primary_channel=channel,
            channel_user_id=str(external_user_id),
            username_or_contact=username,
            first_name=first_name,
            has_name=bool(first_name),
        )
        self.leads[self._lead.lead_id or ""] = self._lead.model_dump()
        return self._lead

    async def save(self, _lead: Lead) -> None:
        if _lead and _lead.lead_id:
            self.leads[_lead.lead_id] = _lead.model_dump()
        return None

    # added for Canon-1 memory contract
    async def get(self, lead_id: str) -> dict | None:
        lead = self.leads.get(lead_id)
        if lead is None and self._lead and self._lead.lead_id == lead_id:
            lead = self._lead.model_dump()
            self.leads[lead_id] = lead
        return self.LeadRecord(lead) if lead else None

    # added for Canon-1 memory contract
    async def update_last_activity(self, lead_id: str, now) -> None:
        lead = self.leads.setdefault(lead_id, {})
        lead["last_activity_at"] = now

    async def fetch_rolling_summary(self, lead_id: str, **kwargs) -> dict | None:
        return None

    async def fetch_daily_summary(self, lead_id: str, **kwargs) -> dict | None:
        return None

    async def get_messages_in_window(self, lead_id: str, **kwargs) -> list[dict]:
        return []
        lead["last_activity_at_iso"] = now.isoformat()

    async def record_extraction_attempt(self, *, lead_id: str | None, attempt: dict[str, object]) -> bool:
        if not lead_id:
            return False
        self.extraction_attempts.setdefault(lead_id, []).append(dict(attempt))
        return True

    # added for Canon-1 memory contract
    async def append_message(
        self,
        *,
        lead_id: str,
        role: str,
        text: str,
        timestamp,
        channel: str | None,
        chat_id: str | None,
        external_user_id: str | None,
        message_idempotency_key: str | None = None,
    ) -> None:
        self.messages.setdefault(lead_id, []).append(
            {
                "role": role,
                "text": text,
                "timestamp": timestamp,
                "channel": channel,
                "chat_id": chat_id,
                "external_user_id": external_user_id,
                "message_idempotency_key": message_idempotency_key,
            }
        )

    # added for Canon-1 memory contract
    async def fetch_last_messages(self, *, lead_id: str, since, limit: int = 30) -> list[dict]:
        entries = [
            message
            for message in self.messages.get(lead_id, [])
            if message.get("timestamp") and message["timestamp"] >= since
        ]
        return entries[-limit:]

    # added for Canon-1 memory contract
    async def fetch_latest_daily_summary(self, *, lead_id: str) -> dict | None:
        return self.daily_summaries.get(lead_id)

    async def apply_lead_patch(self, lead_id: str, lead_patch: dict[str, object]) -> bool:
        lead = self.leads.setdefault(lead_id, {})
        lead.update(lead_patch)
        return True

    # added for Canon-1 memory contract
    async def apply_lead_profile(self, lead_id: str, profile: dict[str, object]) -> bool:
        lead = self.leads.setdefault(lead_id, {})
        lead["lead_profile"] = {**lead.get("lead_profile", {}), **profile}
        return True


class InMemorySessionRepository:
    def __init__(self) -> None:
        self._session = None

    async def get_or_create(
        self,
        *,
        channel: str,
        chat_id: str | int | None,
        external_user_id: str | int | None,
        lead_id: str | None,
    ) -> ChatSession:
        if self._session:
            return self._session
        self._session = ChatSession(
            id=f"{channel}:{external_user_id or chat_id}",
            channel=channel,
            chat_id=str(chat_id) if chat_id is not None else None,
            external_user_id=str(external_user_id or chat_id),
            lead_id=lead_id,
        )
        return self._session

    async def save(self, _session: ChatSession) -> None:
        return None

    async def get(self, _session_id: str) -> ChatSession | None:
        return self._session


def test_dialog_service_stub_reply():
    telegram = FakeTelegramClient()
    leads_repo = InMemoryLeadRepository()
    sessions_repo = InMemorySessionRepository()
    service = DialogService(
        telegram,
        leads_repo=leads_repo,
        sessions_repo=sessions_repo,
        settings=_test_safe_settings(),
    )
    message = {
        "channel": "telegram",
        "chat_id": 123,
        "external_user_id": 456,
        "username": "test_user",
        "first_name": "Test",
        "text": "Привет",
        "message_id": "msg-1",
    }

    result = asyncio.run(service.handle_normalized_message(message))

    assert result.reply_text == ""
    assert result.status == "degraded"
    assert telegram.sent_messages == []
