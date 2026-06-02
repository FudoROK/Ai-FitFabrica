"""Portable SQLAlchemy models for canonical identity state."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import SqlBase


class PersonRow(SqlBase):
    """Canonical person identity row."""

    __tablename__ = "persons"

    person_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LeadRow(SqlBase):
    """Canonical lead ownership row bound to a person."""

    __tablename__ = "leads"

    lead_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    person_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), ForeignKey("persons.person_id"), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    merged_into_lead_id: Mapped[object | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class ChannelIdentityRow(SqlBase):
    """Channel-scoped external identity mapped onto a person."""

    __tablename__ = "channel_identities"
    __table_args__ = (
        UniqueConstraint("channel", "external_identity", name="uq_channel_identities_channel_external_identity"),
    )

    channel_identity_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    person_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), ForeignKey("persons.person_id"), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    external_identity: Mapped[str] = mapped_column(String(255), nullable=False)
    lifecycle_state: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class IdentityBindingRow(SqlBase):
    """Binding between a channel identity and a canonical lead."""

    __tablename__ = "identity_bindings"

    identity_binding_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    channel_identity_id: Mapped[object] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("channel_identities.channel_identity_id"),
        nullable=False,
    )
    lead_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), ForeignKey("leads.lead_id"), nullable=False)
    binding_state: Mapped[str] = mapped_column(String(32), nullable=False)
    decision_basis: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provenance_json: Mapped[dict[str, object]] = mapped_column("provenance", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    superseded_by_binding_id: Mapped[object | None] = mapped_column(Uuid(as_uuid=True), nullable=True)


class IdentityResolutionAuditRow(SqlBase):
    """Audit trail for canonical identity resolution decisions."""

    __tablename__ = "identity_resolution_audit"

    identity_resolution_audit_id: Mapped[object] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    person_id: Mapped[object | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("persons.person_id"), nullable=True)
    lead_id: Mapped[object | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("leads.lead_id"), nullable=True)
    channel_identity_id: Mapped[object | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("channel_identities.channel_identity_id"),
        nullable=True,
    )
    decision_mode: Mapped[str] = mapped_column(String(64), nullable=False)
    external_identity_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    binding_created: Mapped[bool] = mapped_column(nullable=False, default=False)
    person_created: Mapped[bool] = mapped_column(nullable=False, default=False)
    lead_created: Mapped[bool] = mapped_column(nullable=False, default=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


Index("ix_channel_identities_channel_external_identity", ChannelIdentityRow.channel, ChannelIdentityRow.external_identity)
Index("ix_identity_bindings_channel_identity_id_binding_state", IdentityBindingRow.channel_identity_id, IdentityBindingRow.binding_state)
Index("ix_leads_person_id", LeadRow.person_id)
Index("ix_identity_resolution_audit_lead_id_created_at", IdentityResolutionAuditRow.lead_id, IdentityResolutionAuditRow.created_at)
