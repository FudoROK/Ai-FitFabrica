"""Admin-facing merchant workload tier models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.domain.business_catalog import BusinessMerchant
from src.use_cases.business_catalog.tenant_partitioning import (
    BusinessCatalogLoadMetrics,
    BusinessCatalogTenantTier,
)


class BusinessMerchantTierCard(BaseModel):
    """Admin view model for one merchant workload tier decision."""

    model_config = ConfigDict(extra="forbid")

    merchant: BusinessMerchant
    assigned_tier: BusinessCatalogTenantTier
    recommended_tier: BusinessCatalogTenantTier
    recommendation_reasons: list[str]
    metrics: BusinessCatalogLoadMetrics
    queue_partition: str
    storage_prefix: str
    rate_limit_bucket: str
    hot_account_mode: bool
