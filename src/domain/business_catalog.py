"""Domain models for seller-owned B2B product catalog state."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)


class StrictBusinessCatalogModel(BaseModel):
    """Base model for strict business catalog contracts."""

    model_config = ConfigDict(extra="forbid")


class BusinessMerchantStatus(str, Enum):
    """Lifecycle state for a business merchant profile."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class BusinessProductStatus(str, Enum):
    """Lifecycle state for a seller-owned product."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    ACTIVE = "active"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ReviewStatus(str, Enum):
    """Admin review state for catalog visibility."""

    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class SearchIndexStatus(str, Enum):
    """Search indexing lifecycle for approved catalog products."""

    NOT_INDEXED = "not_indexed"
    PENDING = "pending"
    INDEXED = "indexed"
    FAILED = "failed"


class CategoryValidationStatus(str, Enum):
    """Visual category validation state before product approval."""

    NOT_CHECKED = "not_checked"
    MATCHED = "matched"
    MISMATCH = "mismatch"
    UNCERTAIN = "uncertain"


class ProductImageRole(str, Enum):
    """Role of one product image."""

    PRIMARY = "primary"
    GALLERY = "gallery"
    SOURCE = "source"
    GENERATED = "generated"


class ProductAvailability(str, Enum):
    """Sellable offer availability state."""

    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    PREORDER = "preorder"
    UNKNOWN = "unknown"


class CatalogImportStatus(str, Enum):
    """Lifecycle state for a catalog import job."""

    UPLOADED = "uploaded"
    VALIDATING = "validating"
    COMPLETED = "completed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
    FAILED = "failed"


class BusinessMerchant(StrictBusinessCatalogModel):
    """Business seller profile owned by one workspace owner."""

    merchant_id: str = Field(min_length=1, max_length=128)
    owner_id: str = Field(min_length=1, max_length=128)
    display_name: str = Field(min_length=1, max_length=255)
    legal_name: str | None = Field(default=None, max_length=255)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    contact_email: str | None = Field(default=None, max_length=255)
    instagram_url: HttpUrl | None = None
    website_url: HttpUrl | None = None
    status: BusinessMerchantStatus = BusinessMerchantStatus.DRAFT
    assigned_tier: str = Field(default="standard", pattern=r"^(standard|large)$")
    tier_assigned_reason: str | None = Field(default=None, max_length=1000)
    tier_assigned_by: str | None = Field(default=None, max_length=128)
    tier_assigned_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        """Normalize ISO-like country code values."""

        return value.strip().upper()


class BusinessProduct(StrictBusinessCatalogModel):
    """Seller-owned product metadata before public search projection."""

    product_id: str = Field(min_length=1, max_length=128)
    merchant_id: str = Field(min_length=1, max_length=128)
    owner_id: str = Field(min_length=1, max_length=128)
    title: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=4000)
    country_code: str = Field(min_length=2, max_length=2)
    city: str = Field(min_length=1, max_length=128)
    status: BusinessProductStatus = BusinessProductStatus.DRAFT
    review_status: ReviewStatus = ReviewStatus.NOT_REQUIRED
    source_type: str = Field(min_length=1, max_length=64)
    review_reason: str | None = Field(default=None, max_length=1000)
    category_validation_status: CategoryValidationStatus = CategoryValidationStatus.NOT_CHECKED
    category_validation_reason: str | None = Field(default=None, max_length=1000)
    visual_category: str | None = Field(default=None, max_length=128)
    visual_category_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    category_validated_at: datetime | None = None
    search_index_status: SearchIndexStatus = SearchIndexStatus.NOT_INDEXED
    search_index_error: str | None = Field(default=None, max_length=1000)
    search_indexed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("country_code")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        """Normalize ISO-like country code values."""

        return value.strip().upper()


class BusinessProductImage(StrictBusinessCatalogModel):
    """Stored image metadata for a seller product."""

    image_id: str = Field(min_length=1, max_length=128)
    product_id: str = Field(min_length=1, max_length=128)
    object_key: str = Field(min_length=1, max_length=1024)
    content_type: str = Field(min_length=1, max_length=128)
    size_bytes: int = Field(gt=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: ProductImageRole
    sort_order: int = Field(ge=0)
    created_at: datetime = Field(default_factory=utc_now)


class BusinessProductOffer(StrictBusinessCatalogModel):
    """Sellable offer metadata for one seller product."""

    offer_id: str = Field(min_length=1, max_length=128)
    product_id: str = Field(min_length=1, max_length=128)
    price_amount: Decimal = Field(ge=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    availability: ProductAvailability
    product_url: HttpUrl | None = None
    delivery_regions: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        """Normalize ISO-like currency codes."""

        return value.strip().upper()


class CatalogImportJob(StrictBusinessCatalogModel):
    """CSV/Excel import job metadata."""

    import_id: str = Field(min_length=1, max_length=128)
    merchant_id: str = Field(min_length=1, max_length=128)
    owner_id: str = Field(min_length=1, max_length=128)
    filename: str = Field(min_length=1, max_length=255)
    status: CatalogImportStatus
    total_rows: int = Field(ge=0)
    accepted_rows: int = Field(ge=0)
    rejected_rows: int = Field(ge=0)
    error_summary: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def validate_row_counts(self) -> "CatalogImportJob":
        """Prevent impossible import counters."""

        if self.accepted_rows + self.rejected_rows > self.total_rows:
            raise ValueError("accepted_rows + rejected_rows cannot exceed total_rows")
        return self


class CatalogImportRowError(StrictBusinessCatalogModel):
    """One row-level import validation error."""

    import_id: str = Field(min_length=1, max_length=128)
    row_number: int = Field(ge=1)
    field_name: str = Field(min_length=1, max_length=128)
    safe_code: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=500)
