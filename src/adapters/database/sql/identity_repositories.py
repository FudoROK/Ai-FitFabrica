"""PostgreSQL-backed identity-core repository implementations."""

from __future__ import annotations

from datetime import datetime, timezone
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


def _utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def _channel_identity_record_from_row(row: ChannelIdentityRow) -> ChannelIdentityRecord:
    """Map a SQLAlchemy row to the domain channel identity record."""
    return ChannelIdentityRecord(
        channel_identity_id=row.channel_identity_id,
        person_id=row.person_id,
        channel=row.channel,
        external_identity=row.external_identity,
        lifecycle_state=ChannelIdentityState(row.lifecycle_state),
        metadata=dict(row.metadata_json or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
        deprecated_at=row.deprecated_at,
    )


def _lead_record_from_row(row: LeadRow) -> LeadRecord:
    """Map a SQLAlchemy row to the domain lead record."""
    return LeadRecord(
        lead_id=row.lead_id,
        person_id=row.person_id,
        lifecycle_state=LeadLifecycleState(row.lifecycle_state),
        display_name=row.display_name,
        metadata=dict(row.metadata_json or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
        suspended_at=row.suspended_at,
        merged_into_lead_id=row.merged_into_lead_id,
    )


def _identity_binding_record_from_row(row: IdentityBindingRow) -> IdentityBindingRecord:
    """Map a SQLAlchemy row to the domain binding record."""
    return IdentityBindingRecord(
        identity_binding_id=row.identity_binding_id,
        channel_identity_id=row.channel_identity_id,
        lead_id=row.lead_id,
        binding_state=IdentityBindingState(row.binding_state),
        decision_basis=row.decision_basis,
        provenance=dict(row.provenance_json or {}),
        created_at=row.created_at,
        updated_at=row.updated_at,
        revoked_at=row.revoked_at,
        superseded_by_binding_id=row.superseded_by_binding_id,
    )


class SqlChannelIdentityRepository(ChannelIdentityRepository):
    """SQL implementation of the channel identity contract."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared session factory."""
        self._session_factory = session_factory

    async def get_or_create_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
        metadata: dict[str, object] | None = None,
    ) -> ChannelIdentityRecord:
        """Fetch an existing channel identity or create a new canonical one."""
        existing = await self.get_by_channel_external(channel=channel, external_identity=external_identity)
        if existing is not None:
            return existing

        now = _utc_now()
        person_id = uuid4()
        async with self._session_factory() as session:
            session.add(
                PersonRow(
                    person_id=person_id,
                    display_name=None,
                    metadata_json={},
                    created_at=now,
                    updated_at=now,
                )
            )
            row = ChannelIdentityRow(
                channel_identity_id=uuid4(),
                person_id=person_id,
                channel=channel,
                external_identity=external_identity,
                lifecycle_state=ChannelIdentityState.ACTIVE.value,
                metadata_json=dict(metadata or {}),
                created_at=now,
                updated_at=now,
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
        """Look up a channel identity by its stable external key."""
        async with self._session_factory() as session:
            row = await session.scalar(
                select(ChannelIdentityRow).where(
                    ChannelIdentityRow.channel == channel,
                    ChannelIdentityRow.external_identity == external_identity,
                )
            )
            return _channel_identity_record_from_row(row) if row is not None else None

    async def update_state(self, *, channel_identity: ChannelIdentityRecord) -> ChannelIdentityRecord:
        """Persist lifecycle state updates for a channel identity."""
        async with self._session_factory() as session:
            row = await session.get(ChannelIdentityRow, channel_identity.channel_identity_id)
            if row is None:
                raise ValueError("channel identity not found")
            row.lifecycle_state = channel_identity.lifecycle_state.value
            row.metadata_json = dict(channel_identity.metadata)
            row.updated_at = channel_identity.updated_at
            row.deprecated_at = channel_identity.deprecated_at
            await session.commit()
            await session.refresh(row)
            return _channel_identity_record_from_row(row)


class SqlLeadRepository(LeadRepository):
    """SQL implementation of the canonical lead contract."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared session factory."""
        self._session_factory = session_factory

    async def create_lead(self, *, lead: LeadRecord) -> LeadRecord:
        """Insert a canonical lead row."""
        async with self._session_factory() as session:
            row = LeadRow(
                lead_id=lead.lead_id,
                person_id=lead.person_id,
                lifecycle_state=lead.lifecycle_state.value,
                display_name=lead.display_name,
                metadata_json=dict(lead.metadata),
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
        """Fetch a lead by primary key."""
        async with self._session_factory() as session:
            row = await session.get(LeadRow, lead_id)
            return _lead_record_from_row(row) if row is not None else None

    async def update_lead(self, *, lead: LeadRecord) -> LeadRecord:
        """Persist lead mutations."""
        async with self._session_factory() as session:
            row = await session.get(LeadRow, lead.lead_id)
            if row is None:
                raise ValueError("lead not found")
            row.person_id = lead.person_id
            row.lifecycle_state = lead.lifecycle_state.value
            row.display_name = lead.display_name
            row.metadata_json = dict(lead.metadata)
            row.updated_at = lead.updated_at
            row.suspended_at = lead.suspended_at
            row.merged_into_lead_id = lead.merged_into_lead_id
            await session.commit()
            await session.refresh(row)
            return _lead_record_from_row(row)

    async def lookup_lead_by_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
    ) -> LeadRecord | None:
        """Resolve a canonical lead through the stable channel identity row."""
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
    """SQL implementation of the identity binding contract."""

    def __init__(self, *, session_factory) -> None:
        """Store the shared session factory."""
        self._session_factory = session_factory

    async def create_binding(self, *, binding: IdentityBindingRecord) -> IdentityBindingRecord:
        """Insert a new identity binding row."""
        async with self._session_factory() as session:
            row = IdentityBindingRow(
                identity_binding_id=binding.identity_binding_id,
                channel_identity_id=binding.channel_identity_id,
                lead_id=binding.lead_id,
                binding_state=binding.binding_state.value,
                decision_basis=binding.decision_basis,
                provenance_json=dict(binding.provenance),
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
        """Fetch the active binding for a channel identity."""
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
        """Revoke a binding and persist the reason."""
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
        """Mark a binding as superseded by a newer binding."""
        async with self._session_factory() as session:
            row = await session.get(IdentityBindingRow, identity_binding_id)
            if row is None:
                raise ValueError("identity binding not found")
            row.binding_state = IdentityBindingState.SUPERSEDED.value
            row.decision_basis = reason
            row.superseded_by_binding_id = superseded_by_binding_id
            row.updated_at = _utc_now()
            await session.commit()
            await session.refresh(row)
            return _identity_binding_record_from_row(row)

    async def list_bindings_for_lead(self, *, lead_id: UUID) -> list[IdentityBindingRecord]:
        """List all bindings associated with one canonical lead."""
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
        """Update a binding lifecycle state and return the refreshed domain record."""
        async with self._session_factory() as session:
            row = await session.get(IdentityBindingRow, identity_binding_id)
            if row is None:
                raise ValueError("identity binding not found")
            row.binding_state = state.value
            row.decision_basis = reason
            row.updated_at = _utc_now()
            if state == IdentityBindingState.REVOKED:
                row.revoked_at = row.updated_at
            await session.commit()
            await session.refresh(row)
            return _identity_binding_record_from_row(row)
