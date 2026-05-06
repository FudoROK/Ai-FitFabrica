"""Identity binding repository boundary."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ..models.identity_binding import IdentityBindingRecord


class IdentityBindingRepository(Protocol):
    async def create_binding(self, *, binding: IdentityBindingRecord) -> IdentityBindingRecord:
        ...

    async def get_active_binding_for_channel_identity(
        self,
        *,
        channel_identity_id: UUID,
    ) -> IdentityBindingRecord | None:
        ...

    async def revoke_binding(
        self,
        *,
        identity_binding_id: UUID,
        reason: str,
    ) -> IdentityBindingRecord:
        ...

    async def supersede_binding(
        self,
        *,
        identity_binding_id: UUID,
        superseded_by_binding_id: UUID,
        reason: str,
    ) -> IdentityBindingRecord:
        ...

    async def list_bindings_for_lead(self, *, lead_id: UUID) -> list[IdentityBindingRecord]:
        ...
