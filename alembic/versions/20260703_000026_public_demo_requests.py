"""Add public demo request persistence.

Revision ID: 20260703_000026
Revises: 20260702_000025
Create Date: 2026-07-03 00:00:26.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260703_000026"
down_revision = "20260702_000025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create public demo request persistence table."""

    op.create_table(
        "public_demo_requests",
        sa.Column("request_id", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index("ix_public_demo_requests_created_at", "public_demo_requests", ["created_at"])
    op.create_index("ix_public_demo_requests_email", "public_demo_requests", ["email"])
    op.create_index("ix_public_demo_requests_status", "public_demo_requests", ["status"])


def downgrade() -> None:
    """Drop public demo request persistence table."""

    op.drop_index("ix_public_demo_requests_status", table_name="public_demo_requests")
    op.drop_index("ix_public_demo_requests_email", table_name="public_demo_requests")
    op.drop_index("ix_public_demo_requests_created_at", table_name="public_demo_requests")
    op.drop_table("public_demo_requests")
