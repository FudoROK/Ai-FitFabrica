from __future__ import annotations

from datetime import datetime
from typing import Optional, Protocol, TypedDict

from src.domain.models import ChatSession, Lead


class IAsyncExecutor(Protocol):
    async def __call__(self, func, /, *args, **kwargs): ...


class LeadMessageRecord(TypedDict):
    role: str
    text: str
    timestamp: datetime


class DailySummaryRecord(TypedDict, total=False):
    daily_summary: str


class RollingSummaryRecord(TypedDict, total=False):
    rolling_summary_text: str
    open_questions: list[str]
    carry_forward_notes: list[str]
    days_count: int
    last_daily_summary_date: str
    version: int


class LeadRepositoryPort(Protocol):
    async def get(self, lead_id: Optional[str]) -> Optional[Lead]: ...
    async def get_or_create_canonical(
        self,
        *,
        canonical_lead_id: str,
        channel: str,
        external_user_id: str | int | None,
        username: Optional[str],
        first_name: Optional[str],
    ) -> Lead: ...
    async def save(self, lead: Lead) -> None: ...
    async def fetch_last_messages(self, *, lead_id: str, since: datetime, limit: int = 30) -> list[LeadMessageRecord]: ...
    async def fetch_latest_daily_summary(self, *, lead_id: str) -> Optional[DailySummaryRecord]: ...
    async def fetch_rolling_summary(self, *, lead_id: str) -> Optional[RollingSummaryRecord]: ...


class SessionRepositoryPort(Protocol):
    async def get_or_create(
        self,
        *,
        channel: str,
        chat_id: str,
        external_user_id: str,
        lead_id: Optional[str] = None,
    ) -> ChatSession: ...
