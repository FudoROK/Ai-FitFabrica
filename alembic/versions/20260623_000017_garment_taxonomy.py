"""Create garment taxonomy and wear-control review tables."""

from alembic import op
import sqlalchemy as sa

revision = "20260623_000017"
down_revision = "20260615_000016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create backend-owned taxonomy catalog and candidate review tables."""
    op.create_table(
        "garment_taxonomy_items",
        sa.Column("code", sa.String(length=96), nullable=False),
        sa.Column("parent_code", sa.String(length=96), nullable=True),
        sa.Column("category", sa.String(length=96), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_code"], ["garment_taxonomy_items.code"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("code"),
    )
    op.create_index("ix_garment_taxonomy_items_code", "garment_taxonomy_items", ["code"], unique=True)
    op.create_index("ix_garment_taxonomy_items_category", "garment_taxonomy_items", ["category"], unique=False)

    op.create_table(
        "garment_wear_controls",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("taxonomy_item_code", sa.String(length=96), nullable=True),
        sa.Column("parent_category_code", sa.String(length=96), nullable=True),
        sa.Column("control_code", sa.String(length=96), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("instruction_template", sa.Text(), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("default_for_auto", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["taxonomy_item_code"], ["garment_taxonomy_items.code"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("taxonomy_item_code", "parent_category_code", "control_code", name="uq_garment_wear_control_scope"),
    )
    op.create_index("ix_garment_wear_controls_control_code", "garment_wear_controls", ["control_code"], unique=False)
    op.create_index("ix_garment_wear_controls_taxonomy_item", "garment_wear_controls", ["taxonomy_item_code"], unique=False)

    op.create_table(
        "garment_taxonomy_candidates",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("proposed_code", sa.String(length=96), nullable=False),
        sa.Column("proposed_display_name", sa.String(length=160), nullable=False),
        sa.Column("proposed_parent_code", sa.String(length=96), nullable=True),
        sa.Column("proposed_category", sa.String(length=96), nullable=False),
        sa.Column("proposed_controls", sa.JSON(), nullable=False),
        sa.Column("source_job_ids", sa.JSON(), nullable=False),
        sa.Column("examples_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("agent_reasoning_summary", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("reviewed_by", sa.String(length=128), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_reason", sa.Text(), nullable=True),
        sa.Column("approved_catalog_item_code", sa.String(length=96), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approved_catalog_item_code"], ["garment_taxonomy_items.code"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_garment_taxonomy_candidates_status", "garment_taxonomy_candidates", ["status"], unique=False)
    op.create_index("ix_garment_taxonomy_candidates_proposed_code", "garment_taxonomy_candidates", ["proposed_code"], unique=False)

    op.create_table(
        "garment_taxonomy_audit_log",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("actor_id", sa.String(length=128), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=128), nullable=False),
        sa.Column("before_json", sa.JSON(), nullable=False),
        sa.Column("after_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_garment_taxonomy_audit_log_entity",
        "garment_taxonomy_audit_log",
        ["entity_type", "entity_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop garment taxonomy and wear-control review tables."""
    op.drop_index("ix_garment_taxonomy_audit_log_entity", table_name="garment_taxonomy_audit_log")
    op.drop_table("garment_taxonomy_audit_log")
    op.drop_index("ix_garment_taxonomy_candidates_proposed_code", table_name="garment_taxonomy_candidates")
    op.drop_index("ix_garment_taxonomy_candidates_status", table_name="garment_taxonomy_candidates")
    op.drop_table("garment_taxonomy_candidates")
    op.drop_index("ix_garment_wear_controls_taxonomy_item", table_name="garment_wear_controls")
    op.drop_index("ix_garment_wear_controls_control_code", table_name="garment_wear_controls")
    op.drop_table("garment_wear_controls")
    op.drop_index("ix_garment_taxonomy_items_category", table_name="garment_taxonomy_items")
    op.drop_index("ix_garment_taxonomy_items_code", table_name="garment_taxonomy_items")
    op.drop_table("garment_taxonomy_items")
