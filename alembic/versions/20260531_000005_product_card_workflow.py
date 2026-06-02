"""Product-card workflow foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260531_000005"
down_revision = "20260531_000004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create product-card workflow tables."""
    op.create_table(
        "product_card_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("target_channel", sa.String(length=64), nullable=False),
        sa.Column("brand_tone", sa.String(length=128), nullable=False),
        sa.Column("title_hint", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_table(
        "product_card_source_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["product_card_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product_card_versions",
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("bullet_points", sa.JSON(), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["product_card_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_table(
        "product_card_quality_notes",
        sa.Column("note_id", sa.String(length=64), nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["product_card_versions.version_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("note_id"),
    )
    op.create_index("ix_product_card_jobs_status_created_at", "product_card_jobs", ["status", "created_at"], unique=False)
    op.create_index("ix_product_card_versions_job_id_created_at", "product_card_versions", ["job_id", "created_at"], unique=False)


def downgrade() -> None:
    """Drop product-card workflow tables."""
    op.drop_index("ix_product_card_versions_job_id_created_at", table_name="product_card_versions")
    op.drop_index("ix_product_card_jobs_status_created_at", table_name="product_card_jobs")
    op.drop_table("product_card_quality_notes")
    op.drop_table("product_card_versions")
    op.drop_table("product_card_source_assets")
    op.drop_table("product_card_jobs")
