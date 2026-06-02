"""Migration-state Firestore runtime adapters implementing identity-core repository contracts.

These adapters remain only as temporary compatibility fallbacks. New identity-core
feature work should target the portable SQL adapters instead of extending this file.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from src.adapters.database.firestore.firestore_client_factory import firestore, get_firestore_client, safe_execute
from src.identity_core.contracts.channel_identity_repository import ChannelIdentityRepository
from src.identity_core.contracts.identity_binding_repository import IdentityBindingRepository
from src.identity_core.contracts.lead_repository import LeadRepository
from src.identity_core.models.channel_identity import ChannelIdentityRecord
from src.identity_core.models.identity_core_primitives import ChannelIdentityState, IdentityBindingState, LeadLifecycleState
from src.identity_core.models.identity_binding import IdentityBindingRecord
from src.identity_core.models.lead import LeadRecord

_CHANNEL_IDENTITIES_COLLECTION = "identity_core_channel_identities"
_LEADS_COLLECTION = "identity_core_leads"
_BINDINGS_COLLECTION = "identity_core_identity_bindings"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_uuid(raw: Any, *, fallback: UUID | None = None) -> UUID:
    try:
        return UUID(str(raw))
    except Exception:
        return fallback or uuid4()


class FirestoreChannelIdentityRepository(ChannelIdentityRepository):
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

        client = get_firestore_client()
        if not client:
            now = _utc_now()
            return ChannelIdentityRecord(
                channel_identity_id=uuid4(),
                person_id=uuid4(),
                channel=channel,
                external_identity=external_identity,
                lifecycle_state=ChannelIdentityState.ACTIVE,
                metadata=dict(metadata or {}),
                created_at=now,
                updated_at=now,
            )

        now = _utc_now()
        doc_ref = client.collection(_CHANNEL_IDENTITIES_COLLECTION).document(f"{channel}:{external_identity}")
        payload = {
            "channel_identity_id": str(uuid4()),
            "person_id": str(uuid4()),
            "channel": channel,
            "external_identity": external_identity,
            "lifecycle_state": ChannelIdentityState.ACTIVE.value,
            "metadata": dict(metadata or {}),
            "created_at": now,
            "updated_at": now,
        }
        safe_execute(doc_ref.set, payload, merge=False)
        snapshot = safe_execute(doc_ref.get)
        return _channel_identity_from_doc(snapshot.to_dict() or payload)

    async def get_by_channel_external(
        self,
        *,
        channel: str,
        external_identity: str,
    ) -> ChannelIdentityRecord | None:
        client = get_firestore_client()
        if not client:
            return None
        snapshot = safe_execute(client.collection(_CHANNEL_IDENTITIES_COLLECTION).document(f"{channel}:{external_identity}").get)
        if not snapshot or not snapshot.exists:
            return None
        return _channel_identity_from_doc(snapshot.to_dict() or {})

    async def update_state(self, *, channel_identity: ChannelIdentityRecord) -> ChannelIdentityRecord:
        client = get_firestore_client()
        if not client:
            return channel_identity
        doc_ref = client.collection(_CHANNEL_IDENTITIES_COLLECTION).document(
            f"{channel_identity.channel}:{channel_identity.external_identity}"
        )
        safe_execute(
            doc_ref.set,
            {
                "channel_identity_id": str(channel_identity.channel_identity_id),
                "person_id": str(channel_identity.person_id),
                "channel": channel_identity.channel,
                "external_identity": channel_identity.external_identity,
                "lifecycle_state": channel_identity.lifecycle_state.value,
                "metadata": channel_identity.metadata,
                "created_at": channel_identity.created_at,
                "updated_at": _utc_now(),
            },
            merge=True,
        )
        snapshot = safe_execute(doc_ref.get)
        return _channel_identity_from_doc(snapshot.to_dict() or {})


class FirestoreLeadIdentityRepository(LeadRepository):
    async def create_lead(self, *, lead: LeadRecord) -> LeadRecord:
        client = get_firestore_client()
        if not client:
            return lead
        doc_ref = client.collection(_LEADS_COLLECTION).document(str(lead.lead_id))
        safe_execute(
            doc_ref.set,
            {
                "lead_id": str(lead.lead_id),
                "person_id": str(lead.person_id),
                "lifecycle_state": lead.lifecycle_state.value,
                "display_name": lead.display_name,
                "metadata": dict(lead.metadata or {}),
                "created_at": lead.created_at,
                "updated_at": lead.updated_at,
            },
            merge=False,
        )
        snapshot = safe_execute(doc_ref.get)
        return _lead_from_doc(snapshot.to_dict() or {})

    async def get_lead_by_id(self, *, lead_id: UUID) -> LeadRecord | None:
        client = get_firestore_client()
        if not client:
            return None
        snapshot = safe_execute(client.collection(_LEADS_COLLECTION).document(str(lead_id)).get)
        if not snapshot or not snapshot.exists:
            return None
        return _lead_from_doc(snapshot.to_dict() or {})

    async def update_lead(self, *, lead: LeadRecord) -> LeadRecord:
        client = get_firestore_client()
        if not client:
            return lead
        doc_ref = client.collection(_LEADS_COLLECTION).document(str(lead.lead_id))
        safe_execute(
            doc_ref.set,
            {
                "person_id": str(lead.person_id),
                "lifecycle_state": lead.lifecycle_state.value,
                "display_name": lead.display_name,
                "metadata": dict(lead.metadata or {}),
                "updated_at": _utc_now(),
            },
            merge=True,
        )
        snapshot = safe_execute(doc_ref.get)
        return _lead_from_doc(snapshot.to_dict() or {})

    async def lookup_lead_by_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
    ) -> LeadRecord | None:
        client = get_firestore_client()
        if not client:
            return None
        if firestore is None:  # pragma: no cover
            return None
        query = safe_execute(
            client.collection(_LEADS_COLLECTION)
            .where(filter=firestore.FieldFilter("metadata.first_channel", "==", channel))
            .where(filter=firestore.FieldFilter("metadata.first_external_identity", "==", external_identity))
            .limit(1)
            .stream
        )
        docs = list(query)
        if not docs:
            return None
        return _lead_from_doc(docs[0].to_dict() or {})


class FirestoreIdentityBindingRepository(IdentityBindingRepository):
    async def create_binding(self, *, binding: IdentityBindingRecord) -> IdentityBindingRecord:
        client = get_firestore_client()
        if not client:
            return binding
        doc_ref = client.collection(_BINDINGS_COLLECTION).document(str(binding.identity_binding_id))
        safe_execute(
            doc_ref.set,
            {
                "identity_binding_id": str(binding.identity_binding_id),
                "channel_identity_id": str(binding.channel_identity_id),
                "lead_id": str(binding.lead_id),
                "binding_state": binding.binding_state.value,
                "decision_basis": binding.decision_basis,
                "provenance": dict(binding.provenance or {}),
                "created_at": binding.created_at,
                "updated_at": binding.updated_at,
            },
            merge=False,
        )
        snapshot = safe_execute(doc_ref.get)
        return _binding_from_doc(snapshot.to_dict() or {})

    async def get_active_binding_for_channel_identity(
        self,
        *,
        channel_identity_id: UUID,
    ) -> IdentityBindingRecord | None:
        client = get_firestore_client()
        if not client:
            return None
        if firestore is None:  # pragma: no cover
            return None
        query = safe_execute(
            client.collection(_BINDINGS_COLLECTION)
            .where(filter=firestore.FieldFilter("channel_identity_id", "==", str(channel_identity_id)))
            .where(filter=firestore.FieldFilter("binding_state", "==", IdentityBindingState.ACTIVE.value))
            .limit(1)
            .stream
        )
        docs = list(query)
        if not docs:
            return None
        return _binding_from_doc(docs[0].to_dict() or {})

    async def revoke_binding(self, *, identity_binding_id: UUID, reason: str) -> IdentityBindingRecord:
        return await self._set_binding_state(identity_binding_id=identity_binding_id, state=IdentityBindingState.REVOKED, reason=reason)

    async def supersede_binding(
        self,
        *,
        identity_binding_id: UUID,
        superseded_by_binding_id: UUID,
        reason: str,
    ) -> IdentityBindingRecord:
        client = get_firestore_client()
        if not client:
            now = _utc_now()
            return IdentityBindingRecord(
                identity_binding_id=identity_binding_id,
                channel_identity_id=uuid4(),
                lead_id=uuid4(),
                binding_state=IdentityBindingState.SUPERSEDED,
                decision_basis=reason,
                provenance={},
                created_at=now,
                updated_at=now,
                superseded_by_binding_id=superseded_by_binding_id,
            )
        doc_ref = client.collection(_BINDINGS_COLLECTION).document(str(identity_binding_id))
        safe_execute(
            doc_ref.set,
            {
                "binding_state": IdentityBindingState.SUPERSEDED.value,
                "decision_basis": reason,
                "superseded_by_binding_id": str(superseded_by_binding_id),
                "updated_at": _utc_now(),
            },
            merge=True,
        )
        snapshot = safe_execute(doc_ref.get)
        return _binding_from_doc(snapshot.to_dict() or {})

    async def list_bindings_for_lead(self, *, lead_id: UUID) -> list[IdentityBindingRecord]:
        client = get_firestore_client()
        if not client:
            return []
        if firestore is None:  # pragma: no cover
            return []
        query = safe_execute(
            client.collection(_BINDINGS_COLLECTION)
            .where(filter=firestore.FieldFilter("lead_id", "==", str(lead_id)))
            .stream
        )
        return [_binding_from_doc(doc.to_dict() or {}) for doc in query]

    async def _set_binding_state(
        self,
        *,
        identity_binding_id: UUID,
        state: IdentityBindingState,
        reason: str,
    ) -> IdentityBindingRecord:
        client = get_firestore_client()
        if not client:
            now = _utc_now()
            return IdentityBindingRecord(
                identity_binding_id=identity_binding_id,
                channel_identity_id=uuid4(),
                lead_id=uuid4(),
                binding_state=state,
                decision_basis=reason,
                provenance={},
                created_at=now,
                updated_at=now,
            )
        doc_ref = client.collection(_BINDINGS_COLLECTION).document(str(identity_binding_id))
        safe_execute(
            doc_ref.set,
            {
                "binding_state": state.value,
                "decision_basis": reason,
                "updated_at": _utc_now(),
            },
            merge=True,
        )
        snapshot = safe_execute(doc_ref.get)
        return _binding_from_doc(snapshot.to_dict() or {})


def _channel_identity_from_doc(data: dict[str, Any]) -> ChannelIdentityRecord:
    now = _utc_now()
    return ChannelIdentityRecord(
        channel_identity_id=_safe_uuid(data.get("channel_identity_id")),
        person_id=_safe_uuid(data.get("person_id")),
        channel=str(data.get("channel") or "telegram"),
        external_identity=str(data.get("external_identity") or ""),
        lifecycle_state=ChannelIdentityState(str(data.get("lifecycle_state") or ChannelIdentityState.ACTIVE.value)),
        metadata=dict(data.get("metadata") or {}),
        created_at=data.get("created_at") or now,
        updated_at=data.get("updated_at") or now,
        deprecated_at=data.get("deprecated_at"),
    )


def _lead_from_doc(data: dict[str, Any]) -> LeadRecord:
    now = _utc_now()
    lead_id = _safe_uuid(data.get("lead_id"))
    return LeadRecord(
        lead_id=lead_id,
        person_id=_safe_uuid(data.get("person_id"), fallback=lead_id),
        lifecycle_state=LeadLifecycleState(str(data.get("lifecycle_state") or LeadLifecycleState.ACTIVE.value)),
        display_name=data.get("display_name"),
        metadata=dict(data.get("metadata") or {}),
        created_at=data.get("created_at") or now,
        updated_at=data.get("updated_at") or now,
        suspended_at=data.get("suspended_at"),
        merged_into_lead_id=_safe_uuid(data.get("merged_into_lead_id"), fallback=None) if data.get("merged_into_lead_id") else None,
    )


def _binding_from_doc(data: dict[str, Any]) -> IdentityBindingRecord:
    now = _utc_now()
    return IdentityBindingRecord(
        identity_binding_id=_safe_uuid(data.get("identity_binding_id")),
        channel_identity_id=_safe_uuid(data.get("channel_identity_id")),
        lead_id=_safe_uuid(data.get("lead_id")),
        binding_state=IdentityBindingState(str(data.get("binding_state") or IdentityBindingState.ACTIVE.value)),
        decision_basis=data.get("decision_basis"),
        provenance=dict(data.get("provenance") or {}),
        created_at=data.get("created_at") or now,
        updated_at=data.get("updated_at") or now,
        revoked_at=data.get("revoked_at"),
        superseded_by_binding_id=_safe_uuid(data.get("superseded_by_binding_id"), fallback=None) if data.get("superseded_by_binding_id") else None,
    )


class InMemoryChannelIdentityRepository(ChannelIdentityRepository):
    """Test-safe in-memory adapter for channel identity contract."""

    def __init__(self) -> None:
        self._by_key: dict[tuple[str, str], ChannelIdentityRecord] = {}

    async def get_or_create_channel_identity(
        self,
        *,
        channel: str,
        external_identity: str,
        metadata: dict[str, object] | None = None,
    ) -> ChannelIdentityRecord:
        key = (channel, external_identity)
        existing = self._by_key.get(key)
        if existing is not None:
            return existing
        now = _utc_now()
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

    async def supersede_binding(
        self,
        *,
        identity_binding_id: UUID,
        superseded_by_binding_id: UUID,
        reason: str,
    ) -> IdentityBindingRecord:
        binding = await self._set_state(
            identity_binding_id=identity_binding_id,
            state=IdentityBindingState.SUPERSEDED,
            reason=reason,
        )
        updated = binding.model_copy(update={"superseded_by_binding_id": superseded_by_binding_id})
        self._by_id[identity_binding_id] = updated
        return updated

    async def list_bindings_for_lead(self, *, lead_id: UUID) -> list[IdentityBindingRecord]:
        return [binding for binding in self._by_id.values() if binding.lead_id == lead_id]

    async def _set_state(self, *, identity_binding_id: UUID, state: IdentityBindingState, reason: str) -> IdentityBindingRecord:
        binding = self._by_id.get(identity_binding_id)
        if binding is None:
            now = _utc_now()
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

        updated = binding.model_copy(update={"binding_state": state, "decision_basis": reason, "updated_at": _utc_now()})
        self._by_id[identity_binding_id] = updated
        if state != IdentityBindingState.ACTIVE:
            self._active_by_channel_identity.pop(binding.channel_identity_id, None)
        return updated


__all__ = [
    "FirestoreChannelIdentityRepository",
    "FirestoreIdentityBindingRepository",
    "FirestoreLeadIdentityRepository",
    "InMemoryChannelIdentityRepository",
    "InMemoryIdentityBindingRepository",
    "InMemoryLeadIdentityRepository",
]
