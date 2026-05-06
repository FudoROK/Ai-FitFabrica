from __future__ import annotations

from typing import Protocol

from .models import ActiveWindowRecord, ConversationStateRecord


class MemoryLayerPort(Protocol):
    async def list_active_windows(
        self,
        *,
        statuses: list[str] | None = None,
    ) -> list[ActiveWindowRecord]:
        """Return active-window documents filtered by lifecycle status when provided."""

    async def get_active_window(self, *, lead_id: str) -> ActiveWindowRecord | None:
        """Return current active window for lead if present."""

    async def upsert_active_window(self, *, window: ActiveWindowRecord) -> ActiveWindowRecord:
        """Persist active-window state and return stored record."""

    async def get_conversation_state(self, *, lead_id: str) -> ConversationStateRecord | None:
        """Return current conversation-state snapshot for lead if present."""

    async def upsert_conversation_state(self, *, state: ConversationStateRecord) -> ConversationStateRecord:
        """Persist conversation-state snapshot and return stored record."""

    async def delete_conversation_state(self, *, lead_id: str) -> None:
        """Delete conversation-state snapshot for lead if present."""
