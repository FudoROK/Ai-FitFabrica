from __future__ import annotations

from src.use_cases.business_catalog.tenant_partitioning import (
    BusinessCatalogLoadMetrics,
    BusinessCatalogTenantTier,
    TenantPartitionPolicy,
)


def test_standard_tier_uses_shared_partition_and_deterministic_prefixes() -> None:
    policy = TenantPartitionPolicy(shared_partition_count=8)

    decision = policy.resolve(
        owner_id="owner_1",
        merchant_id="merchant_1",
        assigned_tier=BusinessCatalogTenantTier.STANDARD,
    )

    assert decision.assigned_tier is BusinessCatalogTenantTier.STANDARD
    assert decision.queue_partition.startswith("business-catalog-shared-")
    assert decision.storage_prefix.startswith("business-catalog/shared/")
    assert decision.storage_prefix.endswith("/owners/owner_1/merchants/merchant_1")
    assert decision.rate_limit_bucket.startswith("business-catalog:shared:")
    assert decision.hot_account_mode is False


def test_large_tier_uses_dedicated_partition_without_domain_model_changes() -> None:
    policy = TenantPartitionPolicy(shared_partition_count=8)

    decision = policy.resolve(
        owner_id="owner_1",
        merchant_id="merchant_1",
        assigned_tier=BusinessCatalogTenantTier.LARGE,
    )

    assert decision.assigned_tier is BusinessCatalogTenantTier.LARGE
    assert decision.queue_partition == "business-catalog-dedicated-merchant_1"
    assert decision.storage_prefix == "business-catalog/dedicated/merchant_1/owners/owner_1"
    assert decision.rate_limit_bucket == "business-catalog:dedicated:merchant_1"
    assert decision.hot_account_mode is True


def test_recommendation_is_advisory_and_does_not_change_effective_partition() -> None:
    policy = TenantPartitionPolicy(shared_partition_count=8)
    metrics = BusinessCatalogLoadMetrics(
        product_count=20000,
        imports_last_30_days=12,
        largest_import_rows=25000,
        images_last_30_days=50000,
        failed_imports_last_30_days=2,
    )

    decision = policy.resolve(
        owner_id="owner_1",
        merchant_id="merchant_1",
        assigned_tier=BusinessCatalogTenantTier.STANDARD,
        metrics=metrics,
    )

    assert decision.assigned_tier is BusinessCatalogTenantTier.STANDARD
    assert decision.recommended_tier is BusinessCatalogTenantTier.LARGE
    assert "large_catalog" in decision.recommendation_reasons
    assert "large_import" in decision.recommendation_reasons
    assert decision.queue_partition.startswith("business-catalog-shared-")
    assert decision.hot_account_mode is False


def test_low_load_large_account_can_be_recommended_for_standard_but_not_auto_demoted() -> None:
    policy = TenantPartitionPolicy(shared_partition_count=8)
    metrics = BusinessCatalogLoadMetrics(
        product_count=40,
        imports_last_30_days=0,
        largest_import_rows=0,
        images_last_30_days=10,
        failed_imports_last_30_days=0,
    )

    decision = policy.resolve(
        owner_id="owner_1",
        merchant_id="merchant_1",
        assigned_tier=BusinessCatalogTenantTier.LARGE,
        metrics=metrics,
    )

    assert decision.assigned_tier is BusinessCatalogTenantTier.LARGE
    assert decision.recommended_tier is BusinessCatalogTenantTier.STANDARD
    assert "low_load" in decision.recommendation_reasons
    assert decision.queue_partition == "business-catalog-dedicated-merchant_1"
    assert decision.hot_account_mode is True


def test_storage_keys_are_derived_without_cross_merchant_disclosure() -> None:
    policy = TenantPartitionPolicy(shared_partition_count=8)
    decision = policy.resolve(
        owner_id="owner_1",
        merchant_id="merchant_1",
        assigned_tier=BusinessCatalogTenantTier.STANDARD,
    )

    assert decision.product_storage_prefix("product_1") == (
        f"{decision.storage_prefix}/products/product_1"
    )
    assert decision.import_storage_prefix("import_1") == (
        f"{decision.storage_prefix}/imports/import_1"
    )
    assert decision.image_storage_prefix("product_1", "image_1") == (
        f"{decision.storage_prefix}/products/product_1/images/image_1"
    )
    assert "merchant_2" not in decision.storage_prefix
