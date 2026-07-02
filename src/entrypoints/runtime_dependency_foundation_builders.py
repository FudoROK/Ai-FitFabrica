"""Foundation, workspace, and agent runtime builders."""
from __future__ import annotations

from datetime import datetime, timezone

from src.adapters.database.sql.identity_audit import SqlIdentityResolutionAuditRecorder
from src.adapters.agents.adk_agent_gateway import AdkAgentGateway
from src.adapters.agents.object_storage_artifact_resolver import ObjectStorageAgentArtifactResolver
from src.adapters.agents.in_memory_repository import InMemoryAgentInvocationRepository
from src.adapters.database.sql.agent_invocation_repositories import SqlAgentInvocationRepository
from src.adapters.database.sql.identity_repositories import (
    SqlChannelIdentityRepository,
    SqlIdentityBindingRepository,
    SqlLeadRepository,
)
from src.adapters.database.sql.workspace_state_repositories import SqlWorkspaceStateRepository
from src.adapters.workspace.in_memory_repository import InMemoryWorkspaceStateRepository
from src.entrypoints.runtime_dependency_contracts import (
    FitFabricaAgentRuntimeDependencies,
    AgentInvocationRuntimeDependencies,
    IdentityRuntimeRepositories,
    WorkspaceStateRuntimeDependencies,
    _FITFABRICA_AGENT_DEPLOY_CONFIGS,
    _FITFABRICA_AGENT_MODULES,
    load_fitfabrica_agent_deploy_config,
    load_fitfabrica_agent_root,
)
from src.use_cases.workspace.business_profile_service import WorkspaceBusinessProfileService
from src.use_cases.workspace.capability_service import WorkspaceCapabilityService
from src.use_cases.workspace.integration_service import WorkspaceIntegrationService
from src.use_cases.agents.invocation_service import AgentInvocationService


def utc_now():
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc)


def build_identity_runtime_repositories(settings, *, infrastructure) -> IdentityRuntimeRepositories:
    """Build the runtime identity repository bundle for the current environment."""

    from src.identity_core.services.identity_core_runtime_repositories import (
        InMemoryChannelIdentityRepository,
        InMemoryIdentityBindingRepository,
        InMemoryLeadIdentityRepository,
    )

    if getattr(infrastructure, "sql_session_factory", None) is not None:
        return IdentityRuntimeRepositories(
            channel_identity_repo=SqlChannelIdentityRepository(session_factory=infrastructure.sql_session_factory),
            identity_binding_repo=SqlIdentityBindingRepository(session_factory=infrastructure.sql_session_factory),
            lead_repo=SqlLeadRepository(session_factory=infrastructure.sql_session_factory),
        )
    if str(getattr(settings, "environment", "")).strip().lower() == "test":
        return IdentityRuntimeRepositories(
            channel_identity_repo=InMemoryChannelIdentityRepository(),
            identity_binding_repo=InMemoryIdentityBindingRepository(),
            lead_repo=InMemoryLeadIdentityRepository(),
        )
    raise RuntimeError(
        "portable SQL identity runtime is required outside the test environment"
    )


def build_identity_audit_recorder(*, infrastructure):
    """Build the runtime identity audit recorder when SQL infrastructure is configured."""

    return (
        SqlIdentityResolutionAuditRecorder(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else None
    )


def build_workspace_state_runtime_dependencies(*, infrastructure) -> WorkspaceStateRuntimeDependencies:
    """Build the workspace-state runtime bundle for the current settings instance."""

    repository = (
        SqlWorkspaceStateRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryWorkspaceStateRepository()
    )
    return WorkspaceStateRuntimeDependencies(repository=repository)


def build_workspace_business_profile_service(*, repository) -> WorkspaceBusinessProfileService:
    """Build the workspace business-profile service."""

    return WorkspaceBusinessProfileService(repository=repository, clock=utc_now)


def build_workspace_capability_service(*, repository) -> WorkspaceCapabilityService:
    """Build the workspace capability service."""

    return WorkspaceCapabilityService(repository=repository)


def build_workspace_integration_service(*, repository) -> WorkspaceIntegrationService:
    """Build the workspace integrations service."""

    return WorkspaceIntegrationService(repository=repository, clock=utc_now)


def build_fitfabrica_agent_runtime_dependencies(settings, *, providers) -> FitFabricaAgentRuntimeDependencies:
    """Build the FitFabrica product-agent runtime bundle."""

    agent_roots = {
        agent_name: load_fitfabrica_agent_root(module_name)
        for agent_name, module_name in _FITFABRICA_AGENT_MODULES.items()
    }
    deploy_configs = {
        agent_name: load_fitfabrica_agent_deploy_config(module_name, class_name)
        for agent_name, (module_name, class_name) in _FITFABRICA_AGENT_DEPLOY_CONFIGS.items()
    }
    return FitFabricaAgentRuntimeDependencies(
        provider_runtime=providers,
        orchestrator_agent=agent_roots["orchestrator_agent"],
        orchestrator_deploy_config=deploy_configs["orchestrator_agent"],
        user_profile_agent=agent_roots["user_profile_agent"],
        user_profile_deploy_config=deploy_configs["user_profile_agent"],
        business_profile_agent=agent_roots["business_profile_agent"],
        business_profile_deploy_config=deploy_configs["business_profile_agent"],
        human_identity_agent=agent_roots["human_identity_agent"],
        human_identity_deploy_config=deploy_configs["human_identity_agent"],
        garment_identity_agent=agent_roots["garment_identity_agent"],
        garment_identity_deploy_config=deploy_configs["garment_identity_agent"],
        material_texture_agent=agent_roots["material_texture_agent"],
        material_texture_deploy_config=deploy_configs["material_texture_agent"],
        try_on_agent=agent_roots["try_on_agent"],
        try_on_deploy_config=deploy_configs["try_on_agent"],
        quality_verifier_agent=agent_roots["quality_verifier_agent"],
        quality_verifier_deploy_config=deploy_configs["quality_verifier_agent"],
        repair_agent=agent_roots["repair_agent"],
        repair_deploy_config=deploy_configs["repair_agent"],
        fashion_stylist_agent=agent_roots["fashion_stylist_agent"],
        fashion_stylist_deploy_config=deploy_configs["fashion_stylist_agent"],
        marketplace_agent=agent_roots["marketplace_agent"],
        marketplace_deploy_config=deploy_configs["marketplace_agent"],
        trend_agent=agent_roots["trend_agent"],
        trend_deploy_config=deploy_configs["trend_agent"],
        pricing_agent=agent_roots["pricing_agent"],
        pricing_deploy_config=deploy_configs["pricing_agent"],
        product_card_agent=agent_roots["product_card_agent"],
        product_card_deploy_config=deploy_configs["product_card_agent"],
        cost_credits_agent=agent_roots["cost_credits_agent"],
        cost_credits_deploy_config=deploy_configs["cost_credits_agent"],
    )


def build_agent_invocation_runtime_dependencies(settings, *, infrastructure, providers) -> AgentInvocationRuntimeDependencies:
    """Build the canonical agent gateway, audit repository, and invocation service."""

    if providers.agent_runtime is None:
        raise RuntimeError("agent runtime provider is required for canonical agent invocations")
    if getattr(infrastructure, "sql_session_factory", None) is not None:
        repository = SqlAgentInvocationRepository(session_factory=infrastructure.sql_session_factory)
    elif str(getattr(settings, "environment", "")).strip().lower() == "test":
        repository = InMemoryAgentInvocationRepository()
    else:
        raise RuntimeError("portable SQL agent invocation audit repository is required outside tests")
    gateway = AdkAgentGateway(
        agent_runtime=providers.agent_runtime,
        artifact_resolver=ObjectStorageAgentArtifactResolver(
            object_storage=infrastructure.object_storage,
            max_artifact_bytes=int(getattr(settings, "try_on_max_upload_bytes", 10 * 1024 * 1024)),
        ),
    )
    return AgentInvocationRuntimeDependencies(
        gateway=gateway,
        repository=repository,
        invocation_service=AgentInvocationService(gateway=gateway, repository=repository),
    )
