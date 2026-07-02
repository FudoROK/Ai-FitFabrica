"""Tenant partitioning and tier recommendation policy for B2B catalog workloads."""

from __future__ import annotations

from enum import Enum
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field


class BusinessCatalogTenantTier(str, Enum):
    """Admin-assigned workload tier for one business merchant."""

    STANDARD = "standard"
    LARGE = "large"


class BusinessCatalogLoadMetrics(BaseModel):
    """Metrics snapshot used for advisory tier recommendations."""

    model_config = ConfigDict(extra="forbid")

    product_count: int = Field(ge=0)
    imports_last_30_days: int = Field(ge=0)
    largest_import_rows: int = Field(ge=0)
    images_last_30_days: int = Field(ge=0)
    failed_imports_last_30_days: int = Field(ge=0)


class TenantPartitionDecision(BaseModel):
    """Resolved workload partition for one merchant."""

    model_config = ConfigDict(extra="forbid")

    tenant_key: str = Field(min_length=1)
    queue_partition: str = Field(min_length=1)
    storage_prefix: str = Field(min_length=1)
    rate_limit_bucket: str = Field(min_length=1)
    assigned_tier: BusinessCatalogTenantTier
    recommended_tier: BusinessCatalogTenantTier
    recommendation_reasons: list[str] = Field(default_factory=list)
    hot_account_mode: bool

    def product_storage_prefix(self, product_id: str) -> str:
        """Return deterministic product object prefix."""

        return f"{self.storage_prefix}/products/{product_id}"

    def import_storage_prefix(self, import_id: str) -> str:
        """Return deterministic import object prefix."""

        return f"{self.storage_prefix}/imports/{import_id}"

    def image_storage_prefix(self, product_id: str, image_id: str) -> str:
        """Return deterministic product image object prefix."""

        return f"{self.product_storage_prefix(product_id)}/images/{image_id}"


class TenantPartitionPolicy:
    """Resolve current partitions and advisory tier recommendations."""

    def __init__(
        self,
        *,
        shared_partition_count: int = 16,
        large_product_threshold: int = 10_000,
        large_import_rows_threshold: int = 10_000,
        frequent_import_threshold: int = 10,
        high_image_volume_threshold: int = 20_000,
    ) -> None:
        """Store deterministic thresholds for the current catalog tier policy."""

        if shared_partition_count < 1:
            raise ValueError("shared_partition_count must be positive")
        self._shared_partition_count = shared_partition_count
        self._large_product_threshold = large_product_threshold
        self._large_import_rows_threshold = large_import_rows_threshold
        self._frequent_import_threshold = frequent_import_threshold
        self._high_image_volume_threshold = high_image_volume_threshold

    def resolve(
        self,
        *,
        owner_id: str,
        merchant_id: str,
        assigned_tier: BusinessCatalogTenantTier = BusinessCatalogTenantTier.STANDARD,
        metrics: BusinessCatalogLoadMetrics | None = None,
    ) -> TenantPartitionDecision:
        """Resolve effective workload partition from admin-assigned tier only."""

        recommended_tier, reasons = self.recommend(metrics)
        if assigned_tier is BusinessCatalogTenantTier.LARGE:
            return TenantPartitionDecision(
                tenant_key=f"merchant:{merchant_id}",
                queue_partition=f"business-catalog-dedicated-{merchant_id}",
                storage_prefix=f"business-catalog/dedicated/{merchant_id}/owners/{owner_id}",
                rate_limit_bucket=f"business-catalog:dedicated:{merchant_id}",
                assigned_tier=assigned_tier,
                recommended_tier=recommended_tier,
                recommendation_reasons=reasons,
                hot_account_mode=True,
            )
        shard = self._shared_shard(owner_id)
        return TenantPartitionDecision(
            tenant_key=f"owner:{owner_id}",
            queue_partition=f"business-catalog-shared-{shard}",
            storage_prefix=f"business-catalog/shared/{shard}/owners/{owner_id}/merchants/{merchant_id}",
            rate_limit_bucket=f"business-catalog:shared:{shard}",
            assigned_tier=assigned_tier,
            recommended_tier=recommended_tier,
            recommendation_reasons=reasons,
            hot_account_mode=False,
        )

    def recommend(
        self,
        metrics: BusinessCatalogLoadMetrics | None,
    ) -> tuple[BusinessCatalogTenantTier, list[str]]:
        """Return advisory tier recommendation without changing effective routing."""

        if metrics is None:
            return BusinessCatalogTenantTier.STANDARD, ["no_metrics"]
        reasons: list[str] = []
        if metrics.product_count >= self._large_product_threshold:
            reasons.append("large_catalog")
        if metrics.largest_import_rows >= self._large_import_rows_threshold:
            reasons.append("large_import")
        if metrics.imports_last_30_days >= self._frequent_import_threshold:
            reasons.append("frequent_imports")
        if metrics.images_last_30_days >= self._high_image_volume_threshold:
            reasons.append("high_image_volume")
        if reasons:
            return BusinessCatalogTenantTier.LARGE, reasons
        return BusinessCatalogTenantTier.STANDARD, ["low_load"]

    def _shared_shard(self, owner_id: str) -> str:
        digest = sha256(owner_id.encode("utf-8")).hexdigest()
        shard = int(digest[:8], 16) % self._shared_partition_count
        return f"{shard:02d}"
