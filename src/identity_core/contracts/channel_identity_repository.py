"""Channel identity repository boundary."""
from __future__ import annotations

from typing import Protocol

from ..models.channel_identity import ChannelIdentityRecord


class ChannelIdentityRepository(Protocol):
    async def get_or_create_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
        metadata: dict[str, object] | None = None,
    ) -> ChannelIdentityRecord:
        ...

    async def get_by_channel_external(
        self,
        *,
        channel: str,
        external_identity: str,
    ) -> ChannelIdentityRecord | None:
        ...

    async def update_state(self, *, channel_identity: ChannelIdentityRecord) -> ChannelIdentityRecord:
        ...
