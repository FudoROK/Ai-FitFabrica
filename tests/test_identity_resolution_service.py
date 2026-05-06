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


def test_resolution_creates_canonical_lead_and_binding_when_missing() -> None:
    now = datetime.now(timezone.utc)
    channel_identity = ChannelIdentityRecord(
        channel_identity_id=uuid4(),
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
    assert repos.lead.lifecycle_state == LeadLifecycleState.ACTIVE
    assert repos.binding is not None
    assert result.canonical_lead_id == str(repos.binding.lead_id)
