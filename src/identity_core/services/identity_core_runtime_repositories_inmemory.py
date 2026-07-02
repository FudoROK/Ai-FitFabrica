"""In-memory identity runtime adapters for tests and fallback execution."""
from __future__ import annotations

from uuid import UUID, uuid4

from src.identity_core.contracts.channel_identity_repository import ChannelIdentityRepository
from src.identity_core.contracts.identity_binding_repository import IdentityBindingRepository
from src.identity_core.contracts.lead_repository import LeadRepository
from src.identity_core.models.channel_identity import ChannelIdentityRecord
from src.identity_core.models.identity_core_primitives import ChannelIdentityState, IdentityBindingState
from src.identity_core.models.identity_binding import IdentityBindingRecord
from src.identity_core.models.lead import LeadRecord

from .identity_core_runtime_repository_helpers import utc_now


class InMemoryChannelIdentityRepository(ChannelIdentityRepository):
    """Test-safe in-memory adapter for channel identity contract."""

    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], ChannelIdentityRecord] = {}

    async def get_or_create_channel_identity(self, *, channel: str, external_identity: str, metadata: dict[str, object] | None = None) -> ChannelIdentityRecord:
        key = (channel, external_identity)
        existing = self._by_key.get(key)
        if existing is not None:
            return existing
        now = utc_now()
        created = ChannelIdentityRecord(
            channel_identity_id=uuid4(),
            person_id=uuid4(),
            channel=channel,
            external_identity=external_identity,
            lifecycle_state=ChannelIdentityState.ACTIVE,
            metadata=dict(metadata or {}),
            created_at=now,
            updated_at=now,
        )
        self._by_key[key] = created
        return created

    async def get_by_channel_external(self, *, channel: str, external_identity: str) -> ChannelIdentityRecord | None:
        return self._by_key.get((channel, external_identity))

    async def update_state(self, *, channel_identity: ChannelIdentityRecord) -> ChannelIdentityRecord:
        self._by_key[(channel_identity.channel, channel_identity.external_identity)] = channel_identity
        return channel_identity


class InMemoryLeadIdentityRepository(LeadRepository):
    """Test-safe in-memory adapter for lead contract."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, LeadRecord] = {}
        self._by_channel_external: dict[tuple[str, str], UUID] = {}

    async def create_lead(self, *, lead: LeadRecord) -> LeadRecord:
        self._by_id[lead.lead_id] = lead
        key = (str(lead.metadata.get("first_channel", "")), str(lead.metadata.get("first_external_identity", "")))
        if key[0] and key[1]:
            self._by_channel_external[key] = lead.lead_id
        return lead

    async def get_lead_by_id(self, *, lead_id: UUID) -> LeadRecord | None:
        return self._by_id.get(lead_id)

    async def update_lead(self, *, lead: LeadRecord) -> LeadRecord:
        self._by_id[lead.lead_id] = lead
        return lead

    async def lookup_lead_by_channel_identity(self, *, channel: str, external_identity: str) -> LeadRecord | None:
        lead_id = self._by_channel_external.get((channel, external_identity))
        if lead_id is None:
            return None
        return self._by_id.get(lead_id)


class InMemoryIdentityBindingRepository(IdentityBindingRepository):
    """Test-safe in-memory adapter for identity binding contract."""

    def __init__(self) -> None:
        self._by_id: dict[UUID, IdentityBindingRecord] = {}
        self._active_by_channel_identity: dict[UUID, UUID] = {}

    async def create_binding(self, *, binding: IdentityBindingRecord) -> IdentityBindingRecord:
        self._by_id[binding.identity_binding_id] = binding
        if binding.binding_state == IdentityBindingState.ACTIVE:
            self._active_by_channel_identity[binding.channel_identity_id] = binding.identity_binding_id
        return binding

    async def get_active_binding_for_channel_identity(self, *, channel_identity_id: UUID) -> IdentityBindingRecord | None:
        binding_id = self._active_by_channel_identity.get(channel_identity_id)
        if binding_id is None:
            return None
        return self._by_id.get(binding_id)

    async def revoke_binding(self, *, identity_binding_id: UUID, reason: str) -> IdentityBindingRecord:
        return await self._set_state(identity_binding_id=identity_binding_id, state=IdentityBindingState.REVOKED, reason=reason)

    async def supersede_binding(self, *, identity_binding_id: UUID, superseded_by_binding_id: UUID, reason: str) -> IdentityBindingRecord:
        binding = await self._set_state(identity_binding_id=identity_binding_id, state=IdentityBindingState.SUPERSEDED, reason=reason)
        updated = binding.model_copy(update={"superseded_by_binding_id": superseded_by_binding_id})
        self._by_id[identity_binding_id] = updated
        return updated

    async def list_bindings_for_lead(self, *, lead_id: UUID) -> list[IdentityBindingRecord]:
        return [binding for binding in self._by_id.values() if binding.lead_id == lead_id]

    async def _set_state(self, *, identity_binding_id: UUID, state: IdentityBindingState, reason: str) -> IdentityBindingRecord:
        binding = self._by_id.get(identity_binding_id)
        if binding is None:
            now = utc_now()
            binding = IdentityBindingRecord(
                identity_binding_id=identity_binding_id,
                channel_identity_id=uuid4(),
                lead_id=uuid4(),
                binding_state=state,
                decision_basis=reason,
                provenance={},
                created_at=now,
                updated_at=now,
            )
            self._by_id[identity_binding_id] = binding
            return binding
        updated = binding.model_copy(update={"binding_state": state, "decision_basis": reason, "updated_at": utc_now()})
        self._by_id[identity_binding_id] = updated
        if state != IdentityBindingState.ACTIVE:
            self._active_by_channel_identity.pop(binding.channel_identity_id, None)
        return updated
