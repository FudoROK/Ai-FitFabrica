"""Add marketplace discovery candidate review persistence."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260702_000025"
down_revision = "20260701_000024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Persist review-required open-web marketplace discovery candidates."""

    op.create_table(
        "marketplace_discovery_candidates",
        sa.Column("candidate_id", sa.String(length=128), primary_key=True),
        sa.Column("workspace_id", sa.String(length=128), nullable=True),
        sa.Column("business_id", sa.String(length=128), nullable=True),
        sa.Column("connector_kind", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("media_url", sa.Text(), nullable=True),
        sa.Column("source_title", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("brand", sa.String(length=128), nullable=True),
        sa.Column("source_snippet", sa.String(length=512), nullable=True),
        sa.Column("platform_hint", sa.String(length=64), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("country_code", sa.String(length=2), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("price_amount", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=True),
        sa.Column("raw_payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewed_by", sa.String(length=128), nullable=True),
        sa.Column("rejection_reason", sa.String(length=512), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "workspace_id",
            "business_id",
            "source_url",
            name="uq_marketplace_discovery_candidates_scope_source_url",
        ),
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_business_id",
        "marketplace_discovery_candidates",
        ["business_id"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_connector_kind",
        "marketplace_discovery_candidates",
        ["connector_kind"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_created_at",
        "marketplace_discovery_candidates",
        ["created_at"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_scope_status",
        "marketplace_discovery_candidates",
        ["workspace_id", "business_id", "status"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_source_type",
        "marketplace_discovery_candidates",
        ["source_type"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_status",
        "marketplace_discovery_candidates",
        ["status"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_status_source",
        "marketplace_discovery_candidates",
        ["status", "source_type"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_updated_at",
        "marketplace_discovery_candidates",
        ["updated_at"],
    )
    op.create_index(
        "ix_marketplace_discovery_candidates_workspace_id",
        "marketplace_discovery_candidates",
        ["workspace_id"],
    )


def downgrade() -> None:
    """Remove marketplace discovery candidate review persistence."""

    op.drop_index("ix_marketplace_discovery_candidates_status_source", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_status", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_source_type", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_workspace_id", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_updated_at", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_scope_status", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_created_at", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_connector_kind", table_name="marketplace_discovery_candidates")
    op.drop_index("ix_marketplace_discovery_candidates_business_id", table_name="marketplace_discovery_candidates")
    op.drop_table("marketplace_discovery_candidates")
