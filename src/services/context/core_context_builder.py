"""Context orchestration entrypoint."""
from __future__ import annotations

from typing import Any, Optional

from src.memory_layer import MemoryLayerService
from .context_assembler import assemble_core_context_payload
from .context_projection import ContextProjectionService, DEFAULT_LAST_MESSAGES_LIMIT
from src.domain.contracts.persistence import LeadRepositoryPort

async def build_core_context(
    *,
    lead_id: str,
    channel: str,
    external_user_id: Optional[str],
    chat_id: Optional[str],
    leads_repo: Optional[LeadRepositoryPort] = None,
    memory_layer: MemoryLayerService | None = None,
    last_messages_limit: int = DEFAULT_LAST_MESSAGES_LIMIT,
) -> dict[str, Any]:
    projection_service = ContextProjectionService(leads_repo=leads_repo, memory_layer=memory_layer)
    projection = await projection_service.project(
        lead_id=lead_id,
        channel=channel,
        external_user_id=external_user_id,
        chat_id=chat_id,
        last_messages_limit=last_messages_limit,
    )
    return assemble_core_context_payload(projection)
