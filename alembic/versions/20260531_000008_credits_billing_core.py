"""Credits and billing core foundation."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260531_000008"
down_revision = "20260531_000007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create durable credit account and ledger tables."""
    op.create_table(
        "credit_accounts",
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("owner_type", sa.String(length=32), nullable=False),
        sa.Column("available_credits", sa.Integer(), nullable=False),
        sa.Column("reserved_credits", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
        sa.UniqueConstraint("owner_type", "owner_id", name="uq_credit_accounts_owner"),
    )
    op.create_table(
        "credit_ledger_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("account_id", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("credits_delta", sa.Integer(), nullable=False),
        sa.Column("balance_after_event", sa.Integer(), nullable=False),
        sa.Column("workflow_type", sa.String(length=64), nullable=True),
        sa.Column("workflow_reference", sa.String(length=64), nullable=True),
        sa.Column("stage_name", sa.String(length=64), nullable=True),
        sa.Column("charge_policy", sa.String(length=32), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["credit_accounts.account_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_table(
        "workflow_pricing_rules",
        sa.Column("workflow_type", sa.String(length=64), nullable=False),
        sa.Column("base_credits", sa.Integer(), nullable=False),
        sa.Column("free_retry_enabled", sa.Boolean(), nullable=False),
        sa.Column("free_repair_enabled", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("workflow_type"),
    )
    op.create_index(
        "ix_credit_ledger_events_account_created_at",
        "credit_ledger_events",
        ["account_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop durable credit account and ledger tables."""
    op.drop_index("ix_credit_ledger_events_account_created_at", table_name="credit_ledger_events")
    op.drop_table("workflow_pricing_rules")
    op.drop_table("credit_ledger_events")
    op.drop_table("credit_accounts")
