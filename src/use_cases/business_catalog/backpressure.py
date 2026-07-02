"""Backpressure limits for B2B catalog uploads and imports."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from src.use_cases.business_catalog.tenant_partitioning import BusinessCatalogTenantTier


class BusinessCatalogTierLimits(BaseModel):
    """Upload/import limits for one catalog workload tier."""

    model_config = ConfigDict(extra="forbid")

    csv_max_rows: int = Field(gt=0)
    csv_max_bytes: int = Field(gt=0)
    images_per_product: int = Field(gt=0)


class BusinessCatalogBackpressurePolicy:
    """Validate catalog workload size before expensive processing starts."""

    def __init__(
        self,
        *,
        standard_csv_max_rows: int = 1_000,
        standard_csv_max_bytes: int = 5 * 1024 * 1024,
        standard_images_per_product: int = 10,
        large_csv_max_rows: int = 25_000,
        large_csv_max_bytes: int = 50 * 1024 * 1024,
        large_images_per_product: int = 30,
    ) -> None:
        """Store tier-specific upload/import limits."""

        self._limits = {
            BusinessCatalogTenantTier.STANDARD: BusinessCatalogTierLimits(
                csv_max_rows=standard_csv_max_rows,
                csv_max_bytes=standard_csv_max_bytes,
                images_per_product=standard_images_per_product,
            ),
            BusinessCatalogTenantTier.LARGE: BusinessCatalogTierLimits(
                csv_max_rows=large_csv_max_rows,
                csv_max_bytes=large_csv_max_bytes,
                images_per_product=large_images_per_product,
            ),
        }

    def limits_for(self, tier: BusinessCatalogTenantTier) -> BusinessCatalogTierLimits:
        """Return configured limits for one tier."""

        return self._limits[tier]

    def validate_csv(self, *, tier: BusinessCatalogTenantTier, row_count: int, size_bytes: int) -> None:
        """Raise a structured backpressure error if a CSV import exceeds tier limits."""

        limits = self.limits_for(tier)
        if row_count > limits.csv_max_rows:
            raise _backpressure("csv_rows", limits.csv_max_rows, row_count)
        if size_bytes > limits.csv_max_bytes:
            raise _backpressure("csv_bytes", limits.csv_max_bytes, size_bytes)

    def validate_image_count(self, *, tier: BusinessCatalogTenantTier, existing_count: int) -> None:
        """Raise a structured backpressure error if adding one more image exceeds tier limits."""

        limits = self.limits_for(tier)
        actual = existing_count + 1
        if actual > limits.images_per_product:
            raise _backpressure("images_per_product", limits.images_per_product, actual)


def _backpressure(limit_name: str, limit_value: int, actual_value: int):
    from src.use_cases.business_catalog.service import BusinessCatalogBackpressureError

    return BusinessCatalogBackpressureError(
        "Business catalog request exceeds the current workload tier limits.",
        limit_name=limit_name,
        limit_value=limit_value,
        actual_value=actual_value,
    )
