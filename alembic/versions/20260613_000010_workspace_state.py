"""Workspace state foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260613_000010"
down_revision = "20260531_000009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create durable workspace state tables."""
    op.create_table(
        "workspace_business_profiles",
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("owner_id"),
    )
    op.create_table(
        "workspace_integrations",
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("connected_channels", sa.JSON(), nullable=False),
        sa.Column("has_connected_store", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("owner_id"),
    )
    op.create_table(
        "workspace_outfit_builder_requests",
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("owner_id", sa.String(length=128), nullable=False),
        sa.Column("workflow", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("occasion", sa.String(length=255), nullable=False),
        sa.Column("budget", sa.String(length=255), nullable=True),
        sa.Column("base_item", sa.String(length=255), nullable=True),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index(
        "ix_workspace_outfit_builder_requests_owner_id",
        "workspace_outfit_builder_requests",
        ["owner_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop durable workspace state tables."""
    op.drop_index(
        "ix_workspace_outfit_builder_requests_owner_id",
        table_name="workspace_outfit_builder_requests",
    )
    op.drop_table("workspace_outfit_builder_requests")
    op.drop_table("workspace_integrations")
    op.drop_table("workspace_business_profiles")
