"""Add Similar Search click event analytics."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260701_000023"
down_revision = "20260630_000022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create click-event storage for free Similar Search monetization analytics."""

    op.create_table(
        "similar_search_click_events",
        sa.Column("event_id", sa.String(length=128), nullable=False),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("marketplace", sa.String(length=128), nullable=False),
        sa.Column("offer_url", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("user_country_code", sa.String(length=2), nullable=True),
        sa.Column("user_city", sa.String(length=128), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("redirect_allowed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_similar_search_click_events_created_at",
        "similar_search_click_events",
        ["created_at"],
    )
    op.create_index(
        "ix_similar_search_click_events_marketplace",
        "similar_search_click_events",
        ["marketplace"],
    )
    op.create_index(
        "ix_similar_search_click_events_product_created",
        "similar_search_click_events",
        ["product_id", "created_at"],
    )
    op.create_index(
        "ix_similar_search_click_events_product_id",
        "similar_search_click_events",
        ["product_id"],
    )


def downgrade() -> None:
    """Remove Similar Search click-event storage."""

    op.drop_index("ix_similar_search_click_events_product_id", table_name="similar_search_click_events")
    op.drop_index("ix_similar_search_click_events_product_created", table_name="similar_search_click_events")
    op.drop_index("ix_similar_search_click_events_marketplace", table_name="similar_search_click_events")
    op.drop_index("ix_similar_search_click_events_created_at", table_name="similar_search_click_events")
    op.drop_table("similar_search_click_events")
