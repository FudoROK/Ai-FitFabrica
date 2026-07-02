"""Add Try-On wear-control selections to job root."""

from alembic import op
import sqlalchemy as sa

revision = "20260624_000019"
down_revision = "20260623_000018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Persist backend-validated wear-control selections on Try-On jobs."""
    op.add_column(
        "try_on_jobs",
        sa.Column("wear_control_selections", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.alter_column("try_on_jobs", "wear_control_selections", server_default=None)


def downgrade() -> None:
    """Remove persisted wear-control selections from Try-On jobs."""
    op.drop_column("try_on_jobs", "wear_control_selections")
