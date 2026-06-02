"""Pricing workflow foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260531_000007"
down_revision = "20260531_000006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create pricing workflow tables."""
    op.create_table(
        "pricing_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("product_id", sa.String(length=64), nullable=False),
        sa.Column("target_currency", sa.String(length=16), nullable=False),
        sa.Column("desired_margin_percent", sa.Numeric(6, 2), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_table(
        "pricing_recommendations",
        sa.Column("recommendation_id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("recommended_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=16), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("market_min", sa.Numeric(12, 2), nullable=False),
        sa.Column("market_avg", sa.Numeric(12, 2), nullable=False),
        sa.Column("market_max", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["pricing_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("recommendation_id"),
    )
    op.create_index("ix_pricing_jobs_status_created_at", "pricing_jobs", ["status", "created_at"], unique=False)


def downgrade() -> None:
    """Drop pricing workflow tables."""
    op.drop_index("ix_pricing_jobs_status_created_at", table_name="pricing_jobs")
    op.drop_table("pricing_recommendations")
    op.drop_table("pricing_jobs")
