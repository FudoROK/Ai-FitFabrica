"""Portable platform foundation baseline."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260529_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the portable runtime metadata table."""
    op.create_table(
        "portable_runtime_metadata",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    """Drop the portable runtime metadata table."""
    op.drop_table("portable_runtime_metadata")
