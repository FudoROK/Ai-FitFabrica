"""Channel-scoped identity entity."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .identity_core_primitives import ChannelIdentityState, JsonMap


@dataclass(slots=True, frozen=True)
class ChannelIdentityRecord:
    channel_identity_id: UUID
    channel: str
    external_identity: str
    lifecycle_state: ChannelIdentityState
    metadata: JsonMap
    created_at: datetime
    updated_at: datetime
    deprecated_at: datetime | None = None
