"""Runtime boundary for canonical identity resolution in hot path."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from uuid import uuid4

from src.identity_core.contracts.channel_identity_repository import ChannelIdentityRepository
from src.identity_core.contracts.identity_binding_repository import IdentityBindingRepository
from src.identity_core.contracts.lead_repository import LeadRepository
from src.identity_core.models.channel_identity import ChannelIdentityRecord
from src.identity_core.models.identity_core_primitives import ChannelIdentityState, IdentityBindingState, LeadLifecycleState
from src.identity_core.models.identity_binding import IdentityBindingRecord
from src.identity_core.models.lead import LeadRecord
from src.utils.log_redaction import hash_chat_id

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuntimeIdentityResolutionResult:
    canonical_lead_id: str
    channel_identity_id: str
    channel: str
    external_identity: str


class RuntimeIdentityResolutionService:
    """Resolve inbound channel identity into canonical lead identity via identity-core contracts."""

    def __init__(
        self,
        *,
        channel_identity_repo: ChannelIdentityRepository,
        identity_binding_repo: IdentityBindingRepository,
        lead_repo: LeadRepository,
    ) -> None:
        self._channel_identity_repo = channel_identity_repo
        self._identity_binding_repo = identity_binding_repo
        self._lead_repo = lead_repo

    async def resolve(self, *, channel: str, external_identity: str) -> RuntimeIdentityResolutionResult:
        normalized_channel = str(channel or "telegram").strip().lower()
        normalized_external_identity = str(external_identity or "").strip()
        if not normalized_external_identity:
            raise ValueError("external_identity is required")

        channel_identity = await self._channel_identity_repo.get_or_create_channel_identity(
            channel=normalized_channel,
            external_identity=normalized_external_identity,
            metadata={"resolved_at": datetime.now(timezone.utc).isoformat()},
        )

        binding = await self._identity_binding_repo.get_active_binding_for_channel_identity(
            channel_identity_id=channel_identity.channel_identity_id,
        )
        binding_created = False
        if binding is None:
            lead = await self._create_canonical_lead(channel_identity=channel_identity)
            binding = await self._identity_binding_repo.create_binding(
                binding=IdentityBindingRecord(
                    identity_binding_id=uuid4(),
                    channel_identity_id=channel_identity.channel_identity_id,
                    lead_id=lead.lead_id,
                    binding_state=IdentityBindingState.ACTIVE,
                    decision_basis="runtime:auto_create_on_first_contact",
                    provenance={"resolver": "runtime_identity_resolution", "mode": "step_1_3"},
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            binding_created = True

        result = RuntimeIdentityResolutionResult(
            canonical_lead_id=str(binding.lead_id),
            channel_identity_id=str(channel_identity.channel_identity_id),
            channel=normalized_channel,
            external_identity=normalized_external_identity,
        )
        logger.info(
            "identity_resolution_completed",
            extra={
                "channel": result.channel,
                "external_identity_hash": hash_chat_id(result.external_identity),
                "channel_identity_id": result.channel_identity_id,
                "canonical_lead_id": result.canonical_lead_id,
                "binding_created": binding_created,
            },
        )
        return result

    async def _create_canonical_lead(self, *, channel_identity: ChannelIdentityRecord) -> LeadRecord:
        linked = await self._lead_repo.lookup_lead_by_channel_identity(
            channel=channel_identity.channel,
            external_identity=channel_identity.external_identity,
        )
        if linked is not None:
            return linked

        return await self._lead_repo.create_lead(
            lead=LeadRecord(
                lead_id=uuid4(),
                lifecycle_state=LeadLifecycleState.ACTIVE,
                display_name=None,
                metadata={
                    "created_by": "runtime_identity_resolution",
                    "first_channel": channel_identity.channel,
                    "first_external_identity": channel_identity.external_identity,
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )


__all__ = ["RuntimeIdentityResolutionResult", "RuntimeIdentityResolutionService"]
