"""Backward-compatible facade for runtime builder functions."""
from __future__ import annotations

from src.entrypoints.runtime_dependency_foundation_builders import (
    build_agent_invocation_runtime_dependencies,
    build_fitfabrica_agent_runtime_dependencies,
    build_identity_audit_recorder,
    build_identity_runtime_repositories,
    build_workspace_business_profile_service,
    build_workspace_capability_service,
    build_workspace_integration_service,
    build_workspace_state_runtime_dependencies,
    utc_now,
)
from src.entrypoints.runtime_dependency_workflow_builders import (
    build_billing_runtime_dependencies,
    build_business_catalog_search_indexing_runtime_dependencies,
    build_business_catalog_service,
    build_content_package_runtime_dependencies,
    build_pricing_runtime_dependencies,
    build_similar_search_runtime_dependencies,
    build_try_on_runtime_dependencies,
)
from src.entrypoints.runtime_dependency_operations_builders import build_operations_runtime_dependencies
from src.entrypoints.runtime_dependency_product_card_builder import build_product_card_runtime_dependencies

__all__ = [
    "utc_now",
    "build_identity_runtime_repositories",
    "build_identity_audit_recorder",
    "build_try_on_runtime_dependencies",
    "build_similar_search_runtime_dependencies",
    "build_content_package_runtime_dependencies",
    "build_pricing_runtime_dependencies",
    "build_product_card_runtime_dependencies",
    "build_billing_runtime_dependencies",
    "build_business_catalog_service",
    "build_business_catalog_search_indexing_runtime_dependencies",
    "build_workspace_state_runtime_dependencies",
    "build_workspace_business_profile_service",
    "build_workspace_capability_service",
    "build_workspace_integration_service",
    "build_operations_runtime_dependencies",
    "build_fitfabrica_agent_runtime_dependencies",
    "build_agent_invocation_runtime_dependencies",
]
