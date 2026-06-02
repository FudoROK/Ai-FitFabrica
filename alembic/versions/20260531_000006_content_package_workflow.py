"""Content-package workflow foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260531_000006"
down_revision = "20260531_000005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create content-package workflow tables."""
    op.create_table(
        "content_package_jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("product_card_version_id", sa.String(length=64), nullable=False),
        sa.Column("package_name", sa.String(length=128), nullable=False),
        sa.Column("requested_channels", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.create_table(
        "content_package_versions",
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("package_name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["content_package_jobs.job_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("version_id"),
    )
    op.create_table(
        "content_package_artifacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("version_id", sa.String(length=64), nullable=False),
        sa.Column("asset_kind", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("object_key", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["content_package_versions.version_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_content_package_jobs_status_created_at", "content_package_jobs", ["status", "created_at"], unique=False)
    op.create_index("ix_content_package_versions_job_id_created_at", "content_package_versions", ["job_id", "created_at"], unique=False)


def downgrade() -> None:
    """Drop content-package workflow tables."""
    op.drop_index("ix_content_package_versions_job_id_created_at", table_name="content_package_versions")
    op.drop_index("ix_content_package_jobs_status_created_at", table_name="content_package_jobs")
    op.drop_table("content_package_artifacts")
    op.drop_table("content_package_versions")
    op.drop_table("content_package_jobs")
