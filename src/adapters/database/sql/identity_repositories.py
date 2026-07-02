"""PostgreSQL-backed identity-core repository implementations."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import select

from src.identity_core.contracts.channel_identity_repository import ChannelIdentityRepository
from src.identity_core.contracts.identity_binding_repository import IdentityBindingRepository
from src.identity_core.contracts.lead_repository import LeadRepository
from src.identity_core.models.channel_identity import ChannelIdentityRecord
from src.identity_core.models.identity_core_primitives import ChannelIdentityState, IdentityBindingState, LeadLifecycleState
from src.identity_core.models.identity_binding import IdentityBindingRecord
from src.identity_core.models.lead import LeadRecord

from .identity_models import ChannelIdentityRow, IdentityBindingRow, LeadRow, PersonRow
from .identity_repository_mapping import (
    channel_identity_payload_from_row,
    identity_binding_payload_from_row,
    lead_payload_from_row,
)
from .identity_repository_mutations import (
    apply_binding_state,
    apply_channel_identity_state,
    apply_lead_state,
    apply_superseded_binding,
    build_channel_identity_row,
    build_identity_binding_row,
    build_lead_row,
    build_person_row,
    utc_now,
)

def _channel_identity_record_from_row(row: ChannelIdentityRow) -> ChannelIdentityRecord:
    payload = channel_identity_payload_from_row(row)
    return ChannelIdentityRecord(
        channel_identity_id=payload["channel_identity_id"],
        person_id=payload["person_id"],
        channel=payload["channel"],
        external_identity=payload["external_identity"],
        lifecycle_state=ChannelIdentityState(payload["lifecycle_state"]),
        metadata=payload["metadata"],
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
        deprecated_at=payload["deprecated_at"],
    )

def _lead_record_from_row(row: LeadRow) -> LeadRecord:
    payload = lead_payload_from_row(row)
    return LeadRecord(
        lead_id=payload["lead_id"],
        person_id=payload["person_id"],
        lifecycle_state=LeadLifecycleState(payload["lifecycle_state"]),
        display_name=payload["display_name"],
        metadata=payload["metadata"],
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
        suspended_at=payload["suspended_at"],
        merged_into_lead_id=payload["merged_into_lead_id"],
    )

def _identity_binding_record_from_row(row: IdentityBindingRow) -> IdentityBindingRecord:
    payload = identity_binding_payload_from_row(row)
    return IdentityBindingRecord(
        identity_binding_id=payload["identity_binding_id"],
        channel_identity_id=payload["channel_identity_id"],
        lead_id=payload["lead_id"],
        binding_state=IdentityBindingState(payload["binding_state"]),
        decision_basis=payload["decision_basis"],
        provenance=payload["provenance"],
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
        revoked_at=payload["revoked_at"],
        superseded_by_binding_id=payload["superseded_by_binding_id"],
    )

class SqlChannelIdentityRepository(ChannelIdentityRepository):
    def __init__(self, *, session_factory) -> None:
        self._session_factory = session_factory

    async def get_or_create_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
        metadata: dict[str, object] | None = None,
    ) -> ChannelIdentityRecord:
        existing = await self.get_by_channel_external(channel=channel, external_identity=external_identity)
        if existing is not None:
            return existing

        now = utc_now()
        person_id = uuid4()
        async with self._session_factory() as session:
            session.add(build_person_row(person_id=person_id, now=now))
            row = build_channel_identity_row(
                channel_identity_id=uuid4(),
                person_id=person_id,
                channel=channel,
                external_identity=external_identity,
                metadata=metadata,
                now=now,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _channel_identity_record_from_row(row)
    async def get_by_channel_external(
        self,
        *,
        channel: str,
        external_identity: str,
    ) -> ChannelIdentityRecord | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(ChannelIdentityRow).where(
                    ChannelIdentityRow.channel == channel,
                    ChannelIdentityRow.external_identity == external_identity,
                )
            )
            return _channel_identity_record_from_row(row) if row is not None else None
    async def update_state(self, *, channel_identity: ChannelIdentityRecord) -> ChannelIdentityRecord:
        async with self._session_factory() as session:
            row = await session.get(ChannelIdentityRow, channel_identity.channel_identity_id)
            if row is None:
                raise ValueError("channel identity not found")
            apply_channel_identity_state(
                row,
                lifecycle_state=channel_identity.lifecycle_state.value,
                metadata=dict(channel_identity.metadata),
                updated_at=channel_identity.updated_at,
                deprecated_at=channel_identity.deprecated_at,
            )
            await session.commit()
            await session.refresh(row)
            return _channel_identity_record_from_row(row)

class SqlLeadRepository(LeadRepository):
    def __init__(self, *, session_factory) -> None:
        self._session_factory = session_factory

    async def create_lead(self, *, lead: LeadRecord) -> LeadRecord:
        async with self._session_factory() as session:
            row = build_lead_row(
                lead_id=lead.lead_id,
                person_id=lead.person_id,
                lifecycle_state=lead.lifecycle_state.value,
                display_name=lead.display_name,
                metadata=dict(lead.metadata),
                created_at=lead.created_at,
                updated_at=lead.updated_at,
                suspended_at=lead.suspended_at,
                merged_into_lead_id=lead.merged_into_lead_id,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _lead_record_from_row(row)
    async def get_lead_by_id(self, *, lead_id: UUID) -> LeadRecord | None:
        async with self._session_factory() as session:
            row = await session.get(LeadRow, lead_id)
            return _lead_record_from_row(row) if row is not None else None
    async def update_lead(self, *, lead: LeadRecord) -> LeadRecord:
        async with self._session_factory() as session:
            row = await session.get(LeadRow, lead.lead_id)
            if row is None:
                raise ValueError("lead not found")
            apply_lead_state(
                row,
                person_id=lead.person_id,
                lifecycle_state=lead.lifecycle_state.value,
                display_name=lead.display_name,
                metadata=dict(lead.metadata),
                updated_at=lead.updated_at,
                suspended_at=lead.suspended_at,
                merged_into_lead_id=lead.merged_into_lead_id,
            )
            await session.commit()
            await session.refresh(row)
            return _lead_record_from_row(row)
    async def lookup_lead_by_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
    ) -> LeadRecord | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(LeadRow)
                .join(ChannelIdentityRow, LeadRow.person_id == ChannelIdentityRow.person_id)
                .where(
                    ChannelIdentityRow.channel == channel,
                    ChannelIdentityRow.external_identity == external_identity,
                )
            )
            return _lead_record_from_row(row) if row is not None else None

class SqlIdentityBindingRepository(IdentityBindingRepository):
    def __init__(self, *, session_factory) -> None:
        self._session_factory = session_factory

    async def create_binding(self, *, binding: IdentityBindingRecord) -> IdentityBindingRecord:
        async with self._session_factory() as session:
            row = build_identity_binding_row(
                identity_binding_id=binding.identity_binding_id,
                channel_identity_id=binding.channel_identity_id,
                lead_id=binding.lead_id,
                binding_state=binding.binding_state.value,
                decision_basis=binding.decision_basis,
                provenance=dict(binding.provenance),
                created_at=binding.created_at,
                updated_at=binding.updated_at,
                revoked_at=binding.revoked_at,
                superseded_by_binding_id=binding.superseded_by_binding_id,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return _identity_binding_record_from_row(row)
    async def get_active_binding_for_channel_identity(
        self,
        *,
        channel_identity_id: UUID,
    ) -> IdentityBindingRecord | None:
        async with self._session_factory() as session:
            row = await session.scalar(
                select(IdentityBindingRow).where(
                    IdentityBindingRow.channel_identity_id == channel_identity_id,
                    IdentityBindingRow.binding_state == IdentityBindingState.ACTIVE.value,
                )
            )
            return _identity_binding_record_from_row(row) if row is not None else None
    async def revoke_binding(
        self,
        *,
        identity_binding_id: UUID,
        reason: str,
    ) -> IdentityBindingRecord:
        return await self._set_binding_state(
            identity_binding_id=identity_binding_id,
            state=IdentityBindingState.REVOKED,
            reason=reason,
        )
    async def supersede_binding(
        self,
        *,
        identity_binding_id: UUID,
        superseded_by_binding_id: UUID,
        reason: str,
    ) -> IdentityBindingRecord:
        async with self._session_factory() as session:
            row = await session.get(IdentityBindingRow, identity_binding_id)
            if row is None:
                raise ValueError("identity binding not found")
            apply_superseded_binding(
                row,
                superseded_by_binding_id=superseded_by_binding_id,
                reason=reason,
                superseded_state=IdentityBindingState.SUPERSEDED.value,
            )
            await session.commit()
            await session.refresh(row)
            return _identity_binding_record_from_row(row)
    async def list_bindings_for_lead(self, *, lead_id: UUID) -> list[IdentityBindingRecord]:
        async with self._session_factory() as session:
            rows = (
                await session.scalars(select(IdentityBindingRow).where(IdentityBindingRow.lead_id == lead_id))
            ).all()
            return [_identity_binding_record_from_row(row) for row in rows]
    async def _set_binding_state(
        self,
        *,
        identity_binding_id: UUID,
        state: IdentityBindingState,
        reason: str,
    ) -> IdentityBindingRecord:
        async with self._session_factory() as session:
            row = await session.get(IdentityBindingRow, identity_binding_id)
            if row is None:
                raise ValueError("identity binding not found")
            apply_binding_state(
                row,
                state=state.value,
                reason=reason,
                revoked_state=IdentityBindingState.REVOKED.value,
            )
            await session.commit()
            await session.refresh(row)
            return _identity_binding_record_from_row(row)
