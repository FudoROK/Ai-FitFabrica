"""Composition root helpers for runtime service wiring."""
from __future__ import annotations

from src.entrypoints import runtime_dependency_builders as builders
from src.entrypoints import runtime_dependency_contracts as contracts
from src.entrypoints.runtime_dependency_cache import get_or_build_cached
from src.entrypoints.runtime_dependency_lazy_factories import (
    VertexVirtualTryOnClient,
)
from src.services.runtime.portable_infrastructure import build_portable_infrastructure
from src.llm.provider_runtime import ProviderRuntime, build_provider_runtime
from src.adapters.database.sql.garment_taxonomy_repositories import SqlGarmentTaxonomyRepository
from src.adapters.garment_taxonomy.in_memory_repository import build_test_garment_taxonomy_repository
from src.use_cases.garment_taxonomy.service import GarmentTaxonomyService


def portable_infrastructure(settings):
    """Return the cached portable infrastructure bundle for the settings instance."""
    return get_or_build_cached(
        settings,
        attr_name=contracts._PORTABLE_INFRA_ATTR,
        builder=lambda: build_portable_infrastructure(settings),
    )


def identity_runtime_repositories(settings) -> contracts.IdentityRuntimeRepositories:
    """Return the runtime identity repository bundle for the current environment."""
    return get_or_build_cached(
        settings,
        attr_name=contracts._IDENTITY_RUNTIME_ATTR,
        builder=lambda: builders.build_identity_runtime_repositories(
            settings,
            infrastructure=portable_infrastructure(settings),
        ),
    )


def identity_audit_recorder(settings):
    """Return the runtime identity audit recorder when SQL infrastructure is configured."""
    return get_or_build_cached(
        settings,
        attr_name=contracts._IDENTITY_AUDIT_ATTR,
        builder=lambda: builders.build_identity_audit_recorder(infrastructure=portable_infrastructure(settings)),
    )


def provider_runtime(settings) -> ProviderRuntime:
    """Return the cached provider runtime bundle for the settings instance."""
    return get_or_build_cached(
        settings,
        attr_name=contracts._PROVIDER_RUNTIME_ATTR,
        builder=lambda: build_provider_runtime(settings, object_storage=portable_infrastructure(settings).object_storage),
    )


def _billing_enabled(settings) -> bool:
    """Return whether durable billing should be actively enforced for workflows."""
    return bool(getattr(settings, "billing_core_enabled", False))


def _try_on_agent_invocation_service(settings):
    """Return canonical invocation service outside isolated test runtimes."""

    if str(getattr(settings, "environment", "")).strip().lower() == "test":
        return None
    return agent_invocation_runtime_dependencies(settings).invocation_service


def _cached_runtime(settings, *, attr_name: str, builder):
    """Return one cached runtime bundle for the current settings instance."""
    return get_or_build_cached(settings, attr_name=attr_name, builder=builder)


def _cached_workspace_service(settings, *, attr_name: str, builder):
    """Return one cached workspace service bound to the shared workspace repository."""
    return get_or_build_cached(
        settings,
        attr_name=attr_name,
        builder=lambda: builder(repository=workspace_state_runtime_dependencies(settings).repository),
    )


def try_on_runtime_dependencies(settings) -> contracts.TryOnRuntimeDependencies:
    """Return the cached Try-On runtime bundle for the current settings instance."""
    return _cached_runtime(
        settings,
        attr_name=contracts._TRY_ON_RUNTIME_ATTR,
        builder=lambda: builders.build_try_on_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            providers=provider_runtime(settings),
            billing_service=billing_runtime_dependencies(settings).billing_service,
            billing_enabled=_billing_enabled(settings),
            vertex_virtual_try_on_client_factory=VertexVirtualTryOnClient,
            agent_invocation_service=_try_on_agent_invocation_service(settings),
        ),
    )


def similar_search_runtime_dependencies(settings) -> contracts.SimilarSearchRuntimeDependencies:
    """Return the cached similar-search runtime bundle for the current settings instance."""
    return _cached_runtime(
        settings,
        attr_name=contracts._SIMILAR_SEARCH_RUNTIME_ATTR,
        builder=lambda: builders.build_similar_search_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            providers=provider_runtime(settings),
            agent_invocation_service=None
            if str(getattr(settings, "environment", "")).strip().lower() == "test"
            else agent_invocation_runtime_dependencies(settings).invocation_service,
        ),
    )


def product_card_runtime_dependencies(settings) -> contracts.ProductCardRuntimeDependencies:
    """Return the cached product-card runtime bundle for the current settings instance."""
    return _cached_runtime(
        settings,
        attr_name=contracts._PRODUCT_CARD_RUNTIME_ATTR,
        builder=lambda: builders.build_product_card_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            billing_service=billing_runtime_dependencies(settings).billing_service,
            billing_enabled=_billing_enabled(settings),
            agent_invocation_service=agent_invocation_runtime_dependencies(settings).invocation_service,
        ),
    )


def content_package_runtime_dependencies(settings) -> contracts.ContentPackageRuntimeDependencies:
    """Return the cached content-package runtime bundle for the current settings instance."""
    return _cached_runtime(
        settings,
        attr_name=contracts._CONTENT_PACKAGE_RUNTIME_ATTR,
        builder=lambda: builders.build_content_package_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            billing_service=billing_runtime_dependencies(settings).billing_service,
            billing_enabled=_billing_enabled(settings),
        ),
    )


def pricing_runtime_dependencies(settings) -> contracts.PricingRuntimeDependencies:
    """Return the cached pricing runtime bundle for the current settings instance."""
    return _cached_runtime(
        settings,
        attr_name=contracts._PRICING_RUNTIME_ATTR,
        builder=lambda: builders.build_pricing_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            billing_service=billing_runtime_dependencies(settings).billing_service,
            billing_enabled=_billing_enabled(settings),
        ),
    )


def billing_runtime_dependencies(settings) -> contracts.BillingRuntimeDependencies:
    """Return the cached billing runtime bundle for the current settings instance."""
    return get_or_build_cached(
        settings,
        attr_name=contracts._BILLING_RUNTIME_ATTR,
        builder=lambda: builders.build_billing_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
        ),
    )


def workspace_state_runtime_dependencies(settings) -> contracts.WorkspaceStateRuntimeDependencies:
    """Return the cached workspace-state runtime bundle for the current settings instance."""
    return get_or_build_cached(
        settings,
        attr_name=contracts._WORKSPACE_STATE_RUNTIME_ATTR,
        builder=lambda: builders.build_workspace_state_runtime_dependencies(
            infrastructure=portable_infrastructure(settings),
        ),
    )


def workspace_business_profile_service(settings):
    """Return the cached workspace business-profile service for the current settings instance."""
    return _cached_workspace_service(
        settings,
        attr_name=contracts._WORKSPACE_BUSINESS_PROFILE_SERVICE_ATTR,
        builder=builders.build_workspace_business_profile_service,
    )


def workspace_capability_service(settings):
    """Return the cached workspace capability service for the current settings instance."""
    return _cached_workspace_service(
        settings,
        attr_name=contracts._WORKSPACE_CAPABILITY_SERVICE_ATTR,
        builder=builders.build_workspace_capability_service,
    )


def workspace_integration_service(settings):
    """Return the cached workspace integrations service for the current settings instance."""
    return _cached_workspace_service(
        settings,
        attr_name=contracts._WORKSPACE_INTEGRATION_SERVICE_ATTR,
        builder=builders.build_workspace_integration_service,
    )


def business_catalog_service(settings):
    """Return the cached backend-owned business catalog service."""

    return get_or_build_cached(
        settings,
        attr_name=contracts._BUSINESS_CATALOG_SERVICE_ATTR,
        builder=lambda: builders.build_business_catalog_service(
            settings,
            infrastructure=portable_infrastructure(settings),
            agent_invocation_service=None
            if str(getattr(settings, "environment", "")).strip().lower() == "test"
            else agent_invocation_runtime_dependencies(settings).invocation_service,
        ),
    )


def business_catalog_search_indexing_runtime_dependencies(
    settings,
) -> contracts.BusinessCatalogSearchIndexingRuntimeDependencies:
    """Return the cached backend-owned business catalog search indexing runtime."""

    return _cached_runtime(
        settings,
        attr_name=contracts._BUSINESS_CATALOG_SEARCH_INDEXING_RUNTIME_ATTR,
        builder=lambda: builders.build_business_catalog_search_indexing_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            providers=provider_runtime(settings),
        ),
    )


def garment_taxonomy_service(settings) -> GarmentTaxonomyService | None:
    """Return cached garment taxonomy service when SQL storage is configured."""
    return get_or_build_cached(
        settings,
        attr_name=contracts._GARMENT_TAXONOMY_SERVICE_ATTR,
        builder=lambda: _build_garment_taxonomy_service(settings),
    )


def _build_garment_taxonomy_service(settings) -> GarmentTaxonomyService | None:
    infrastructure = portable_infrastructure(settings)
    if getattr(infrastructure, "sql_session_factory", None) is None:
        if str(getattr(settings, "environment", "")).strip().lower() == "test":
            return GarmentTaxonomyService(repository=build_test_garment_taxonomy_repository())
        return None
    return GarmentTaxonomyService(
        repository=SqlGarmentTaxonomyRepository(session_factory=infrastructure.sql_session_factory)
    )


def operations_runtime_dependencies(settings) -> contracts.OperationsRuntimeDependencies:
    """Return the cached operations runtime bundle for the current settings instance."""
    return _cached_runtime(
        settings,
        attr_name=contracts._OPERATIONS_RUNTIME_ATTR,
        builder=lambda: builders.build_operations_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            try_on_runtime=lambda: try_on_runtime_dependencies(settings),
            product_card_runtime=lambda: product_card_runtime_dependencies(settings),
            content_package_runtime=lambda: content_package_runtime_dependencies(settings),
            pricing_runtime=lambda: pricing_runtime_dependencies(settings),
            business_catalog_search_index_runtime=lambda: business_catalog_search_indexing_runtime_dependencies(settings),
        ),
    )


def fitfabrica_agent_runtime_dependencies(settings) -> contracts.FitFabricaAgentRuntimeDependencies:
    """Return the cached FitFabrica product-agent runtime bundle."""
    return _cached_runtime(
        settings,
        attr_name=contracts._FITFABRICA_AGENT_RUNTIME_ATTR,
        builder=lambda: builders.build_fitfabrica_agent_runtime_dependencies(
            settings,
            providers=provider_runtime(settings),
        ),
    )


def agent_invocation_runtime_dependencies(settings) -> contracts.AgentInvocationRuntimeDependencies:
    """Return the cached canonical agent invocation runtime bundle."""

    return _cached_runtime(
        settings,
        attr_name=contracts._AGENT_INVOCATION_RUNTIME_ATTR,
        builder=lambda: builders.build_agent_invocation_runtime_dependencies(
            settings,
            infrastructure=portable_infrastructure(settings),
            providers=provider_runtime(settings),
        ),
    )
