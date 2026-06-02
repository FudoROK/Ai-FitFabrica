from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from src.identity_core.models.channel_identity import ChannelIdentityRecord
from src.identity_core.models.identity_core_primitives import ChannelIdentityState, IdentityBindingState, LeadLifecycleState
from src.identity_core.models.identity_binding import IdentityBindingRecord
from src.identity_core.models.lead import LeadRecord
from src.identity_core.services.identity_resolution import RuntimeIdentityResolutionService


@dataclass
class _Repos:
    channel_identity: ChannelIdentityRecord
    binding: IdentityBindingRecord | None = None
    lead: LeadRecord | None = None

    async def get_or_create_channel_identity(self, *, channel: str, external_identity: str, metadata=None):
        return self.channel_identity

    async def get_active_binding_for_channel_identity(self, *, channel_identity_id):
        return self.binding

    async def create_binding(self, *, binding: IdentityBindingRecord):
        self.binding = binding
        return binding

    async def lookup_lead_by_channel_identity(self, *, channel: str, external_identity: str):
        return self.lead

    async def create_lead(self, *, lead: LeadRecord):
        self.lead = lead
        return lead


def test_resolution_reuses_existing_binding() -> None:
    now = datetime.now(timezone.utc)
    channel_identity = ChannelIdentityRecord(
        channel_identity_id=uuid4(),
        person_id=uuid4(),
        channel="telegram",
        external_identity="42",
        lifecycle_state=ChannelIdentityState.ACTIVE,
        metadata={},
        created_at=now,
        updated_at=now,
    )
    bound_lead_id = uuid4()
    repos = _Repos(
        channel_identity=channel_identity,
        binding=IdentityBindingRecord(
            identity_binding_id=uuid4(),
            channel_identity_id=channel_identity.channel_identity_id,
            lead_id=bound_lead_id,
            binding_state=IdentityBindingState.ACTIVE,
            decision_basis="existing",
            provenance={},
            created_at=now,
            updated_at=now,
        ),
    )
    service = RuntimeIdentityResolutionService(
        channel_identity_repo=repos,
        identity_binding_repo=repos,
        lead_repo=repos,
    )

    result = asyncio.run(service.resolve(channel="telegram", external_identity="42"))

    assert result.canonical_lead_id == str(bound_lead_id)
    assert result.binding_created is False


def test_resolution_creates_canonical_lead_and_binding_when_missing() -> None:
    now = datetime.now(timezone.utc)
    channel_identity = ChannelIdentityRecord(
        channel_identity_id=uuid4(),
        person_id=uuid4(),
        channel="telegram",
        external_identity="99",
        lifecycle_state=ChannelIdentityState.ACTIVE,
        metadata={},
        created_at=now,
        updated_at=now,
    )
    repos = _Repos(channel_identity=channel_identity)
    service = RuntimeIdentityResolutionService(
        channel_identity_repo=repos,
        identity_binding_repo=repos,
        lead_repo=repos,
    )

    result = asyncio.run(service.resolve(channel="telegram", external_identity="99"))

    assert repos.lead is not None
    assert repos.lead.person_id == channel_identity.person_id
    assert repos.lead.person_id is not None
    assert repos.lead.lifecycle_state == LeadLifecycleState.ACTIVE
    assert repos.binding is not None
    assert result.canonical_lead_id == str(repos.binding.lead_id)
    assert result.binding_created is True


def test_resolution_reuses_existing_lead_without_marking_lead_created() -> None:
    now = datetime.now(timezone.utc)
    person_id = uuid4()
    channel_identity = ChannelIdentityRecord(
        channel_identity_id=uuid4(),
        person_id=person_id,
        channel="telegram",
        external_identity="77",
        lifecycle_state=ChannelIdentityState.ACTIVE,
        metadata={},
        created_at=now,
        updated_at=now,
    )
    existing_lead = LeadRecord(
        lead_id=uuid4(),
        person_id=person_id,
        lifecycle_state=LeadLifecycleState.ACTIVE,
        display_name=None,
        metadata={"first_channel": "telegram", "first_external_identity": "77"},
        created_at=now,
        updated_at=now,
    )
    repos = _Repos(channel_identity=channel_identity, lead=existing_lead)
    service = RuntimeIdentityResolutionService(
        channel_identity_repo=repos,
        identity_binding_repo=repos,
        lead_repo=repos,
    )

    result = asyncio.run(service.resolve(channel="telegram", external_identity="77"))

    assert result.binding_created is True
    assert result.person_created is False
    assert result.lead_created is False
    assert repos.binding is not None
    assert repos.binding.lead_id == existing_lead.lead_id


def test_resolution_records_audit_when_recorder_is_configured() -> None:
    now = datetime.now(timezone.utc)
    channel_identity = ChannelIdentityRecord(
        channel_identity_id=uuid4(),
        person_id=uuid4(),
        channel="telegram",
        external_identity="55",
        lifecycle_state=ChannelIdentityState.ACTIVE,
        metadata={},
        created_at=now,
        updated_at=now,
    )
    repos = _Repos(channel_identity=channel_identity)

    class _AuditRecorder:
        def __init__(self) -> None:
            self.entries = []

        async def record(self, *, entry) -> None:
            self.entries.append(entry)

    audit_recorder = _AuditRecorder()
    service = RuntimeIdentityResolutionService(
        channel_identity_repo=repos,
        identity_binding_repo=repos,
        lead_repo=repos,
        audit_recorder=audit_recorder,
    )

    result = asyncio.run(service.resolve(channel="telegram", external_identity="55"))

    assert result.binding_created is True
    assert len(audit_recorder.entries) == 1
    assert audit_recorder.entries[0].channel_identity_id == channel_identity.channel_identity_id
