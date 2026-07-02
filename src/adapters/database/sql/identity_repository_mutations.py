"""Mutation helpers for SQL identity repositories."""

from __future__ import annotations

from datetime import datetime, timezone

from .identity_models import ChannelIdentityRow, IdentityBindingRow, LeadRow, PersonRow


def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


def build_person_row(*, person_id, now: datetime) -> PersonRow:
    """Build a new person row for first-seen channel identities."""
    return PersonRow(
        person_id=person_id,
        display_name=None,
        metadata_json={},
        created_at=now,
        updated_at=now,
    )


def build_channel_identity_row(
    *,
    channel_identity_id,
    person_id,
    channel: str,
    external_identity: str,
    metadata: dict[str, object] | None,
    now: datetime,
) -> ChannelIdentityRow:
    """Build a new channel-identity row."""
    return ChannelIdentityRow(
        channel_identity_id=channel_identity_id,
        person_id=person_id,
        channel=channel,
        external_identity=external_identity,
        lifecycle_state="active",
        metadata_json=dict(metadata or {}),
        created_at=now,
        updated_at=now,
    )


def apply_channel_identity_state(
    row: ChannelIdentityRow,
    *,
    lifecycle_state: str,
    metadata: dict[str, object],
    updated_at: datetime,
    deprecated_at,
) -> None:
    """Apply channel-identity state onto a persisted row."""
    row.lifecycle_state = lifecycle_state
    row.metadata_json = dict(metadata)
    row.updated_at = updated_at
    row.deprecated_at = deprecated_at


def build_lead_row(
    *,
    lead_id,
    person_id,
    lifecycle_state: str,
    display_name,
    metadata: dict[str, object],
    created_at: datetime,
    updated_at: datetime,
    suspended_at,
    merged_into_lead_id,
) -> LeadRow:
    """Build a new lead row from plain payload fields."""
    return LeadRow(
        lead_id=lead_id,
        person_id=person_id,
        lifecycle_state=lifecycle_state,
        display_name=display_name,
        metadata_json=dict(metadata),
        created_at=created_at,
        updated_at=updated_at,
        suspended_at=suspended_at,
        merged_into_lead_id=merged_into_lead_id,
    )


def apply_lead_state(
    row: LeadRow,
    *,
    person_id,
    lifecycle_state: str,
    display_name,
    metadata: dict[str, object],
    updated_at: datetime,
    suspended_at,
    merged_into_lead_id,
) -> None:
    """Apply lead state onto a persisted row."""
    row.person_id = person_id
    row.lifecycle_state = lifecycle_state
    row.display_name = display_name
    row.metadata_json = dict(metadata)
    row.updated_at = updated_at
    row.suspended_at = suspended_at
    row.merged_into_lead_id = merged_into_lead_id


def build_identity_binding_row(
    *,
    identity_binding_id,
    channel_identity_id,
    lead_id,
    binding_state: str,
    decision_basis: str,
    provenance: dict[str, object],
    created_at: datetime,
    updated_at: datetime,
    revoked_at,
    superseded_by_binding_id,
) -> IdentityBindingRow:
    """Build a new identity-binding row from plain payload fields."""
    return IdentityBindingRow(
        identity_binding_id=identity_binding_id,
        channel_identity_id=channel_identity_id,
        lead_id=lead_id,
        binding_state=binding_state,
        decision_basis=decision_basis,
        provenance_json=dict(provenance),
        created_at=created_at,
        updated_at=updated_at,
        revoked_at=revoked_at,
        superseded_by_binding_id=superseded_by_binding_id,
    )


def apply_superseded_binding(
    row: IdentityBindingRow,
    *,
    superseded_by_binding_id,
    reason: str,
    superseded_state: str,
) -> None:
    """Mark a binding row as superseded by a newer binding."""
    row.binding_state = superseded_state
    row.decision_basis = reason
    row.superseded_by_binding_id = superseded_by_binding_id
    row.updated_at = utc_now()


def apply_binding_state(
    row: IdentityBindingRow,
    *,
    state: str,
    reason: str,
    revoked_state: str,
) -> None:
    """Apply a lifecycle-state transition to a binding row."""
    row.binding_state = state
    row.decision_basis = reason
    row.updated_at = utc_now()
    if state == revoked_state:
        row.revoked_at = row.updated_at
