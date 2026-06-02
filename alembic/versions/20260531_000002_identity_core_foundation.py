"""Identity core foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260531_000002"
down_revision = "20260529_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create canonical identity tables."""
    op.create_table(
        "persons",
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("person_id"),
    )
    op.create_table(
        "leads",
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("suspended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("merged_into_lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["persons.person_id"]),
        sa.PrimaryKeyConstraint("lead_id"),
    )
    op.create_table(
        "channel_identities",
        sa.Column("channel_identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel", sa.String(length=64), nullable=False),
        sa.Column("external_identity", sa.String(length=255), nullable=False),
        sa.Column("lifecycle_state", sa.String(length=32), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deprecated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["person_id"], ["persons.person_id"]),
        sa.PrimaryKeyConstraint("channel_identity_id"),
        sa.UniqueConstraint("channel", "external_identity", name="uq_channel_identities_channel_external_identity"),
    )
    op.create_table(
        "identity_bindings",
        sa.Column("identity_binding_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("channel_identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("binding_state", sa.String(length=32), nullable=False),
        sa.Column("decision_basis", sa.String(length=255), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("superseded_by_binding_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["channel_identity_id"], ["channel_identities.channel_identity_id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.lead_id"]),
        sa.PrimaryKeyConstraint("identity_binding_id"),
    )
    op.create_table(
        "identity_resolution_audit",
        sa.Column("identity_resolution_audit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("channel_identity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decision_mode", sa.String(length=64), nullable=False),
        sa.Column("external_identity_hash", sa.String(length=255), nullable=False),
        sa.Column("binding_created", sa.Boolean(), nullable=False),
        sa.Column("person_created", sa.Boolean(), nullable=False),
        sa.Column("lead_created", sa.Boolean(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["person_id"], ["persons.person_id"]),
        sa.ForeignKeyConstraint(["lead_id"], ["leads.lead_id"]),
        sa.ForeignKeyConstraint(["channel_identity_id"], ["channel_identities.channel_identity_id"]),
        sa.PrimaryKeyConstraint("identity_resolution_audit_id"),
    )
    op.create_index(
        "ix_channel_identities_channel_external_identity",
        "channel_identities",
        ["channel", "external_identity"],
        unique=False,
    )
    op.create_index(
        "ix_identity_bindings_channel_identity_id_binding_state",
        "identity_bindings",
        ["channel_identity_id", "binding_state"],
        unique=False,
    )
    op.create_index("ix_leads_person_id", "leads", ["person_id"], unique=False)
    op.create_index(
        "ix_identity_resolution_audit_lead_id_created_at",
        "identity_resolution_audit",
        ["lead_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop canonical identity tables."""
    op.drop_index("ix_identity_resolution_audit_lead_id_created_at", table_name="identity_resolution_audit")
    op.drop_index("ix_leads_person_id", table_name="leads")
    op.drop_index("ix_identity_bindings_channel_identity_id_binding_state", table_name="identity_bindings")
    op.drop_index("ix_channel_identities_channel_external_identity", table_name="channel_identities")
    op.drop_table("identity_resolution_audit")
    op.drop_table("identity_bindings")
    op.drop_table("channel_identities")
    op.drop_table("leads")
    op.drop_table("persons")
