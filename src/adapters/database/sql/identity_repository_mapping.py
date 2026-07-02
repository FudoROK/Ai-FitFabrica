"""Row-to-domain mapping helpers for SQL identity repositories."""

from __future__ import annotations

from .identity_models import ChannelIdentityRow, IdentityBindingRow, LeadRow


def channel_identity_payload_from_row(row: ChannelIdentityRow) -> dict[str, object]:
    """Map a SQLAlchemy channel-identity row to plain payload data."""
    return {
        "channel_identity_id": row.channel_identity_id,
        "person_id": row.person_id,
        "channel": row.channel,
        "external_identity": row.external_identity,
        "lifecycle_state": row.lifecycle_state,
        "metadata": dict(row.metadata_json or {}),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "deprecated_at": row.deprecated_at,
    }


def lead_payload_from_row(row: LeadRow) -> dict[str, object]:
    """Map a SQLAlchemy lead row to plain payload data."""
    return {
        "lead_id": row.lead_id,
        "person_id": row.person_id,
        "lifecycle_state": row.lifecycle_state,
        "display_name": row.display_name,
        "metadata": dict(row.metadata_json or {}),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "suspended_at": row.suspended_at,
        "merged_into_lead_id": row.merged_into_lead_id,
    }


def identity_binding_payload_from_row(row: IdentityBindingRow) -> dict[str, object]:
    """Map a SQLAlchemy binding row to plain payload data."""
    return {
        "identity_binding_id": row.identity_binding_id,
        "channel_identity_id": row.channel_identity_id,
        "lead_id": row.lead_id,
        "binding_state": row.binding_state,
        "decision_basis": row.decision_basis,
        "provenance": dict(row.provenance_json or {}),
        "created_at": row.created_at,
        "updated_at": row.updated_at,
        "revoked_at": row.revoked_at,
        "superseded_by_binding_id": row.superseded_by_binding_id,
    }
