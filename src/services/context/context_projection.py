"""Projection/read-model adapter for runtime context construction."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from src.memory_layer import MemoryLayerService
from src.domain.contracts.persistence import LeadRepositoryPort

MESSAGE_TTL_DAYS = 180
DEFAULT_LAST_MESSAGES_LIMIT = 30


@dataclass(frozen=True)
class ContextProjection:
    identity: dict[str, Any]
    lead_snapshot: dict[str, Any]
    memory: dict[str, Any]

class ContextProjectionService:
    """Loads storage state and normalizes it into assembler-ready shape."""

    def __init__(
        self,
        *,
        leads_repo: Optional[LeadRepositoryPort] = None,
        memory_layer: MemoryLayerService | None = None,
    ) -> None:
        self._repo = leads_repo
        if self._repo is None:
            raise RuntimeError("LeadRepositoryPort must be provided")
        self._memory_layer = memory_layer
        if self._memory_layer is None:
            raise RuntimeError("MemoryLayerService must be provided")

    async def project(
        self,
        *,
        lead_id: str,
        channel: str,
        external_user_id: Optional[str],
        chat_id: Optional[str],
        last_messages_limit: int = DEFAULT_LAST_MESSAGES_LIMIT,
    ) -> ContextProjection:
        safe_channel = channel or "telegram"
        safe_external_id = str(external_user_id or chat_id or "unknown")

        identity = {
            "channel": safe_channel,
            "external_user_id": safe_external_id,
            "chat_id": str(chat_id) if chat_id is not None else None,
            "lead_id": lead_id,
        }

        now = datetime.now(tz=timezone.utc)
        cutoff = now - timedelta(days=MESSAGE_TTL_DAYS)

        lead_snapshot: dict[str, Any] = {}
        lead = await self._repo.get(str(lead_id))
        if isinstance(lead, dict):
            lead_snapshot = lead
        elif lead is not None and callable(getattr(lead, "model_dump", None)):
            lead_snapshot = lead.model_dump(mode="python")
        memory_bundle = await self._memory_layer.build_read_bundle(
            lead_id=str(lead_id),
            lead=lead,
            leads_repo=self._repo,
            since=cutoff,
            last_messages_limit=last_messages_limit,
        )
        memory_payload = memory_bundle.model_dump(mode="python")
        memory_payload["messages"] = [message.model_dump(mode="python") for message in memory_bundle.messages]

        return ContextProjection(
            identity=identity,
            lead_snapshot=lead_snapshot,
            memory=memory_payload,
        )
