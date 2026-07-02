"""Shared helpers for Firestore-backed identity runtime repositories."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from src.identity_core.models.channel_identity import ChannelIdentityRecord
from src.identity_core.models.identity_core_primitives import ChannelIdentityState, IdentityBindingState, LeadLifecycleState
from src.identity_core.models.identity_binding import IdentityBindingRecord
from src.identity_core.models.lead import LeadRecord


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def safe_uuid(raw: object, *, fallback: UUID | None = None) -> UUID:
    try:
        return UUID(str(raw))
    except Exception:
        return fallback or uuid4()


def _metadata_from_doc(data: dict[str, object]) -> dict[str, object]:
    metadata = data.get("metadata")
    return dict(metadata) if isinstance(metadata, dict) else {}


def _provenance_from_doc(data: dict[str, object]) -> dict[str, object]:
    provenance = data.get("provenance")
    return dict(provenance) if isinstance(provenance, dict) else {}


def channel_identity_from_doc(data: dict[str, object]) -> ChannelIdentityRecord:
    now = utc_now()
    return ChannelIdentityRecord(
        channel_identity_id=safe_uuid(data.get("channel_identity_id")),
        person_id=safe_uuid(data.get("person_id")),
        channel=str(data.get("channel") or "telegram"),
        external_identity=str(data.get("external_identity") or ""),
        lifecycle_state=ChannelIdentityState(str(data.get("lifecycle_state") or ChannelIdentityState.ACTIVE.value)),
        metadata=_metadata_from_doc(data),
        created_at=data.get("created_at") or now,
        updated_at=data.get("updated_at") or now,
        deprecated_at=data.get("deprecated_at"),
    )


def lead_from_doc(data: dict[str, object]) -> LeadRecord:
    now = utc_now()
    lead_id = safe_uuid(data.get("lead_id"))
    return LeadRecord(
        lead_id=lead_id,
        person_id=safe_uuid(data.get("person_id"), fallback=lead_id),
        lifecycle_state=LeadLifecycleState(str(data.get("lifecycle_state") or LeadLifecycleState.ACTIVE.value)),
        display_name=data.get("display_name"),
        metadata=_metadata_from_doc(data),
        created_at=data.get("created_at") or now,
        updated_at=data.get("updated_at") or now,
        suspended_at=data.get("suspended_at"),
        merged_into_lead_id=safe_uuid(data.get("merged_into_lead_id"), fallback=None) if data.get("merged_into_lead_id") else None,
    )


def binding_from_doc(data: dict[str, object]) -> IdentityBindingRecord:
    now = utc_now()
    return IdentityBindingRecord(
        identity_binding_id=safe_uuid(data.get("identity_binding_id")),
        channel_identity_id=safe_uuid(data.get("channel_identity_id")),
        lead_id=safe_uuid(data.get("lead_id")),
        binding_state=IdentityBindingState(str(data.get("binding_state") or IdentityBindingState.ACTIVE.value)),
        decision_basis=data.get("decision_basis"),
        provenance=_provenance_from_doc(data),
        created_at=data.get("created_at") or now,
        updated_at=data.get("updated_at") or now,
        revoked_at=data.get("revoked_at"),
        superseded_by_binding_id=safe_uuid(data.get("superseded_by_binding_id"), fallback=None) if data.get("superseded_by_binding_id") else None,
    )
