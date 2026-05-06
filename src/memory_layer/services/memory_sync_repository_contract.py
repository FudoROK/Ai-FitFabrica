from __future__ import annotations

from datetime import datetime
from typing import Protocol, Optional


class MemorySyncLeadRepository(Protocol):
    """Canonical repository contract required by the memory sync pipeline."""

    async def get(self, lead_id: Optional[str]):
        ...

    async def fetch_daily_summary(self, *, lead_id: str, memory_day_key: str) -> Optional[dict]:
        ...

    async def write_daily_summary(
        self,
        *,
        lead_id: str,
        memory_day_key: str,
        summary_text: str,
        open_questions: list[str],
        carry_forward_notes: list[str],
        learned_facts: list[str],
        changed_facts: list[str],
        memory_relevance_flags: list[str],
        created_at: datetime,
        messages_used_count: Optional[int] = None,
        source_window_start: Optional[datetime] = None,
        source_window_end: Optional[datetime] = None,
    ) -> bool:
        ...

    async def get_messages_in_window(
        self,
        *,
        lead_id: str,
        start_utc: datetime,
        end_utc: datetime,
        limit: int = 200,
    ) -> list[dict]:
        ...

    async def fetch_rolling_summary(self, *, lead_id: str) -> Optional[dict]:
        ...

    async def create_rolling_artifact(
        self,
        *,
        lead_id: str,
        artifact_id: str,
        artifact_payload: dict[str, object],
    ) -> bool:
        ...

    async def promote_rolling_pointer(
        self,
        *,
        lead_id: str,
        artifact_id: str,
        pointer_payload: dict[str, object],
    ) -> bool:
        ...

    async def fetch_current_rolling_pointer(self, *, lead_id: str) -> Optional[dict]:
        ...

    async def fetch_rolling_artifact(self, *, lead_id: str, artifact_id: str) -> Optional[dict]:
        ...

    async def update_rolling_summary(
        self,
        *,
        lead_id: str,
        rolling_update: dict[str, object],
        updated_at: datetime,
    ) -> bool:
        ...

    async def acquire_memory_write_guard(
        self,
        *,
        lead_id: str,
        idempotency_key: str,
        created_at: datetime,
    ) -> bool:
        ...

    async def release_memory_write_guard(self, *, lead_id: str, idempotency_key: str) -> None:
        ...

    async def upsert_crm_contact_binding(
        self,
        *,
        lead_id: str,
        crm_contact_ref: str,
        crm_provider: str,
    ) -> bool:
        ...
