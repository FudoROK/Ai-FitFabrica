"""Seed baseline garment taxonomy and wear controls."""

from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "20260624_000020"
down_revision = "20260624_000019"
branch_labels = None
depends_on = None


taxonomy_items = sa.table(
    "garment_taxonomy_items",
    sa.column("code", sa.String),
    sa.column("parent_code", sa.String),
    sa.column("category", sa.String),
    sa.column("display_name", sa.String),
    sa.column("description", sa.Text),
    sa.column("active", sa.Boolean),
    sa.column("version", sa.Integer),
    sa.column("created_at", sa.DateTime(timezone=True)),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

wear_controls = sa.table(
    "garment_wear_controls",
    sa.column("id", sa.String),
    sa.column("taxonomy_item_code", sa.String),
    sa.column("parent_category_code", sa.String),
    sa.column("control_code", sa.String),
    sa.column("display_name", sa.String),
    sa.column("description", sa.Text),
    sa.column("instruction_template", sa.Text),
    sa.column("risk_level", sa.String),
    sa.column("default_for_auto", sa.Boolean),
    sa.column("active", sa.Boolean),
    sa.column("version", sa.Integer),
)

SEEDED_ITEM_CODES = (
    "shirt",
    "t_shirt",
    "blouse",
    "hoodie",
    "jacket",
    "coat",
    "dress",
    "pants",
    "jeans",
    "skirt",
)

SEEDED_CONTROL_IDS = (
    "wc_shirt_auto",
    "wc_shirt_untucked",
    "wc_shirt_tucked",
    "wc_blouse_auto",
    "wc_blouse_untucked",
    "wc_blouse_tucked",
    "wc_t_shirt_auto",
    "wc_t_shirt_untucked",
    "wc_t_shirt_tucked",
    "wc_hoodie_auto",
    "wc_hoodie_untucked",
    "wc_jacket_auto",
    "wc_jacket_open_front",
    "wc_jacket_buttoned_closed",
    "wc_coat_auto",
    "wc_coat_open_front",
    "wc_dress_auto",
    "wc_pants_auto",
    "wc_pants_high_waist",
    "wc_pants_natural_waist",
    "wc_jeans_auto",
    "wc_jeans_high_waist",
    "wc_jeans_natural_waist",
    "wc_skirt_auto",
    "wc_skirt_high_waist",
    "wc_skirt_natural_waist",
)


def upgrade() -> None:
    """Insert baseline catalog rows required for reproducible staging acceptance."""
    now = datetime(2026, 6, 24, tzinfo=timezone.utc)
    op.bulk_insert(taxonomy_items, [
            _item("shirt", "top", "Shirt", "Button shirt or structured shirt.", now),
            _item("t_shirt", "top", "T-Shirt", "Knitted T-shirt or tee.", now),
            _item("blouse", "top", "Blouse", "Soft woven blouse.", now),
            _item("hoodie", "top", "Hoodie", "Hoodie or sweatshirt.", now),
            _item("jacket", "outerwear", "Jacket", "Jacket, blazer, or light outerwear.", now),
            _item("coat", "outerwear", "Coat", "Coat or heavy outerwear.", now),
            _item("dress", "full_body", "Dress", "Dress or full-body garment.", now),
            _item("pants", "bottom", "Pants", "Pants or trousers.", now),
            _item("jeans", "bottom", "Jeans", "Denim jeans.", now),
            _item("skirt", "bottom", "Skirt", "Skirt.", now),
        ],
    )
    op.bulk_insert(wear_controls, [
            _control("wc_shirt_auto", "shirt", "auto", "Auto", "Use the most natural shirt styling for the outfit without forcing tuck or untuck.", True),
            _control("wc_shirt_untucked", "shirt", "untucked", "Wear untucked", "Keep the shirt worn outside the waistband with a natural hem fall.", False),
            _control("wc_shirt_tucked", "shirt", "tucked", "Tuck in", "Tuck the shirt into the waistband while preserving the original shirt shape and visible details.", False),
            _control("wc_blouse_auto", "blouse", "auto", "Auto", "Use the most natural blouse styling for the outfit without forcing tuck or untuck.", True),
            _control("wc_blouse_untucked", "blouse", "untucked", "Wear untucked", "Keep the blouse worn outside the waistband with a natural drape.", False),
            _control("wc_blouse_tucked", "blouse", "tucked", "Tuck in", "Tuck the blouse into the waistband while preserving fabric drape.", False),
            _control("wc_t_shirt_auto", "t_shirt", "auto", "Auto", "Use the most natural T-shirt styling for the outfit.", True),
            _control("wc_t_shirt_untucked", "t_shirt", "untucked", "Wear untucked", "Keep the T-shirt worn outside the waistband with a natural hem.", False),
            _control("wc_t_shirt_tucked", "t_shirt", "tucked", "Tuck in", "Tuck the T-shirt into the waistband without distorting the body or fabric.", False),
            _control("wc_hoodie_auto", "hoodie", "auto", "Auto", "Use the most natural hoodie styling for the outfit.", True),
            _control("wc_hoodie_untucked", "hoodie", "untucked", "Wear untucked", "Keep the hoodie outside the waistband with natural volume.", False),
            _control("wc_jacket_auto", "jacket", "auto", "Auto", "Use the most natural jacket styling for the outfit.", True),
            _control("wc_jacket_open_front", "jacket", "open_front", "Open front", "Keep the jacket open at the front, preserving lapels, closure details, and garment length.", False),
            _control("wc_jacket_buttoned_closed", "jacket", "buttoned_closed", "Closed", "Show the jacket closed only if closure is visually plausible and does not hide key garment details.", False),
            _control("wc_coat_auto", "coat", "auto", "Auto", "Use the most natural coat styling for the outfit.", True),
            _control("wc_coat_open_front", "coat", "open_front", "Open front", "Keep the coat open at the front, preserving outerwear silhouette and length.", False),
            _control("wc_dress_auto", "dress", "auto", "Auto", "Preserve the dress as a full-body garment with natural fit and length.", True),
            _control("wc_pants_auto", "pants", "auto", "Auto", "Use the most natural pants waist placement for the outfit.", True),
            _control("wc_pants_high_waist", "pants", "high_waist", "High waist", "Place the pants at a high waist only if it remains anatomically natural.", False),
            _control("wc_pants_natural_waist", "pants", "natural_waist", "Natural waist", "Place the pants at the natural waist without changing body proportions.", False),
            _control("wc_jeans_auto", "jeans", "auto", "Auto", "Use the most natural jeans waist placement for the outfit.", True),
            _control("wc_jeans_high_waist", "jeans", "high_waist", "High waist", "Place the jeans at a high waist only if it remains anatomically natural.", False),
            _control("wc_jeans_natural_waist", "jeans", "natural_waist", "Natural waist", "Place the jeans at the natural waist without changing body proportions.", False),
            _control("wc_skirt_auto", "skirt", "auto", "Auto", "Use the most natural skirt waist placement for the outfit.", True),
            _control("wc_skirt_high_waist", "skirt", "high_waist", "High waist", "Place the skirt at a high waist only if it remains anatomically natural.", False),
            _control("wc_skirt_natural_waist", "skirt", "natural_waist", "Natural waist", "Place the skirt at the natural waist without changing body proportions.", False),
        ],
    )


def downgrade() -> None:
    """Remove only rows inserted by this seed migration."""
    op.execute(wear_controls.delete().where(wear_controls.c.id.in_(SEEDED_CONTROL_IDS)))
    op.execute(taxonomy_items.delete().where(taxonomy_items.c.code.in_(SEEDED_ITEM_CODES)))


def _item(code: str, category: str, display_name: str, description: str, now: datetime) -> dict[str, object]:
    return {
        "code": code,
        "parent_code": None,
        "category": category,
        "display_name": display_name,
        "description": description,
        "active": True,
        "version": 1,
        "created_at": now,
        "updated_at": now,
    }


def _control(
    row_id: str,
    item_code: str,
    control_code: str,
    display_name: str,
    instruction_template: str,
    default_for_auto: bool,
) -> dict[str, object]:
    return {
        "id": row_id,
        "taxonomy_item_code": item_code,
        "parent_category_code": None,
        "control_code": control_code,
        "display_name": display_name,
        "description": instruction_template,
        "instruction_template": instruction_template,
        "risk_level": "low",
        "default_for_auto": default_for_auto,
        "active": True,
        "version": 1,
    }
