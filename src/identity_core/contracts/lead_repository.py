"""Lead repository boundary for identity core."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ..models.lead import LeadRecord


class LeadRepository(Protocol):
    async def create_lead(self, *, lead: LeadRecord) -> LeadRecord:
        ...

    async def get_lead_by_id(self, *, lead_id: UUID) -> LeadRecord | None:
        ...

    async def update_lead(self, *, lead: LeadRecord) -> LeadRecord:
        ...

    async def lookup_lead_by_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
    ) -> LeadRecord | None:
        ...
