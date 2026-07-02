"""Agent invocation audit ledger."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260614_000011"
down_revision = "20260613_000010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the safe agent invocation audit ledger."""

    op.create_table(
        "agent_invocations",
        sa.Column("invocation_id", sa.String(length=128), nullable=False),
        sa.Column("trace_id", sa.String(length=128), nullable=False),
        sa.Column("agent_name", sa.String(length=128), nullable=False),
        sa.Column("prompt_version", sa.String(length=128), nullable=False),
        sa.Column("contract_version", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=128), nullable=True),
        sa.Column("model", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("cost_metadata", sa.JSON(), nullable=False),
        sa.Column("input_fields", sa.JSON(), nullable=False),
        sa.Column("output_fields", sa.JSON(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("invocation_id"),
    )
    op.create_index("ix_agent_invocations_trace_id", "agent_invocations", ["trace_id"], unique=False)
    op.create_index("ix_agent_invocations_agent_name", "agent_invocations", ["agent_name"], unique=False)
    op.create_index("ix_agent_invocations_status", "agent_invocations", ["status"], unique=False)
    op.create_index(
        "ix_agent_invocations_agent_started_at",
        "agent_invocations",
        ["agent_name", "started_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop the agent invocation audit ledger."""

    op.drop_index("ix_agent_invocations_agent_started_at", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_status", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_agent_name", table_name="agent_invocations")
    op.drop_index("ix_agent_invocations_trace_id", table_name="agent_invocations")
    op.drop_table("agent_invocations")

