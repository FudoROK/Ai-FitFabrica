"""Contracts and cache keys for runtime dependency wiring."""
from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING

from src.llm.provider_runtime import ProviderRuntime
from src.use_cases.billing import BillingService
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.agents.ports import AgentInvocationPort, AgentInvocationRepositoryPort
from src.use_cases.business_catalog.search_indexing import BusinessCatalogSearchIndexingService
from src.use_cases.business_catalog.search_indexing_workflow import BusinessCatalogSearchIndexingWorkflow
from src.use_cases.content_package.workflow_service import ContentPackageWorkflowService
from src.use_cases.operations import OperationsHealthService, WorkflowDispatchService
from src.use_cases.pricing.workflow_service import PricingWorkflowService
from src.use_cases.product_card.workflow_service import ProductCardWorkflowService
from src.use_cases.similar_search.workflow_service import SimilarSearchWorkflowService
from src.use_cases.similar_search.events import SimilarSearchClickEventService
from src.use_cases.try_on.ports import (
    GarmentIdentityAnalysisPort,
    HumanIdentityAnalysisPort,
    MaterialTextureAnalysisPort,
    TryOnInstructionPort,
    TryOnFileStoragePort,
    TryOnGenerationPort,
    TryOnJobRepositoryPort,
    TryOnRepairPort,
)
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundleService
from src.use_cases.try_on.workflow_service import TryOnWorkflowService
from src.use_cases.workspace.ports import WorkspaceStateRepositoryPort
from src.services.workers.worker_runtime import WorkerRuntime

if TYPE_CHECKING:
    class BaseAgent:  # pragma: no cover - typing-only placeholder for lazy ADK roots
        ...

    from src.adk_agents.business_profile_agent.deploy_config import BusinessProfileAgentDeployConfig
    from src.adk_agents.cost_credits_agent.deploy_config import CostCreditsAgentDeployConfig
    from src.adk_agents.fashion_stylist_agent.deploy_config import FashionStylistAgentDeployConfig
    from src.adk_agents.garment_identity_agent.deploy_config import GarmentIdentityAgentDeployConfig
    from src.adk_agents.human_identity_agent.deploy_config import HumanIdentityAgentDeployConfig
    from src.adk_agents.marketplace_agent.deploy_config import MarketplaceAgentDeployConfig
    from src.adk_agents.material_texture_agent.deploy_config import MaterialTextureAgentDeployConfig
    from src.adk_agents.orchestrator_agent.deploy_config import OrchestratorAgentDeployConfig
    from src.adk_agents.pricing_agent.deploy_config import PricingAgentDeployConfig
    from src.adk_agents.product_card_agent.deploy_config import ProductCardAgentDeployConfig
    from src.adk_agents.quality_verifier_agent.deploy_config import QualityVerifierAgentDeployConfig
    from src.adk_agents.repair_agent.deploy_config import RepairAgentDeployConfig
    from src.adk_agents.trend_agent.deploy_config import TrendAgentDeployConfig
    from src.adk_agents.try_on_agent.deploy_config import TryOnAgentDeployConfig
    from src.adk_agents.user_profile_agent.deploy_config import UserProfileAgentDeployConfig


_PORTABLE_INFRA_ATTR = "_portable_infrastructure"
_IDENTITY_RUNTIME_ATTR = "_identity_runtime_repositories"
_IDENTITY_AUDIT_ATTR = "_identity_audit_recorder"
_PROVIDER_RUNTIME_ATTR = "_provider_runtime"
_TRY_ON_RUNTIME_ATTR = "_try_on_runtime_dependencies"
_SIMILAR_SEARCH_RUNTIME_ATTR = "_similar_search_runtime_dependencies"
_PRODUCT_CARD_RUNTIME_ATTR = "_product_card_runtime_dependencies"
_CONTENT_PACKAGE_RUNTIME_ATTR = "_content_package_runtime_dependencies"
_PRICING_RUNTIME_ATTR = "_pricing_runtime_dependencies"
_BILLING_RUNTIME_ATTR = "_billing_runtime_dependencies"
_OPERATIONS_RUNTIME_ATTR = "_operations_runtime_dependencies"
_WORKSPACE_STATE_RUNTIME_ATTR = "_workspace_state_runtime_dependencies"
_WORKSPACE_BUSINESS_PROFILE_SERVICE_ATTR = "_workspace_business_profile_service"
_WORKSPACE_CAPABILITY_SERVICE_ATTR = "_workspace_capability_service"
_WORKSPACE_INTEGRATION_SERVICE_ATTR = "_workspace_integration_service"
_BUSINESS_CATALOG_SERVICE_ATTR = "_business_catalog_service"
_BUSINESS_CATALOG_SEARCH_INDEXING_RUNTIME_ATTR = "_business_catalog_search_indexing_runtime_dependencies"
_GARMENT_TAXONOMY_SERVICE_ATTR = "_garment_taxonomy_service"
_FITFABRICA_AGENT_RUNTIME_ATTR = "_fitfabrica_agent_runtime_dependencies"
_AGENT_INVOCATION_RUNTIME_ATTR = "_agent_invocation_runtime_dependencies"

_FITFABRICA_AGENT_MODULES = {
    "orchestrator_agent": "src.adk_agents.orchestrator_agent.agent",
    "user_profile_agent": "src.adk_agents.user_profile_agent.agent",
    "business_profile_agent": "src.adk_agents.business_profile_agent.agent",
    "human_identity_agent": "src.adk_agents.human_identity_agent.agent",
    "garment_identity_agent": "src.adk_agents.garment_identity_agent.agent",
    "material_texture_agent": "src.adk_agents.material_texture_agent.agent",
    "try_on_agent": "src.adk_agents.try_on_agent.agent",
    "quality_verifier_agent": "src.adk_agents.quality_verifier_agent.agent",
    "repair_agent": "src.adk_agents.repair_agent.agent",
    "fashion_stylist_agent": "src.adk_agents.fashion_stylist_agent.agent",
    "marketplace_agent": "src.adk_agents.marketplace_agent.agent",
    "trend_agent": "src.adk_agents.trend_agent.agent",
    "pricing_agent": "src.adk_agents.pricing_agent.agent",
    "product_card_agent": "src.adk_agents.product_card_agent.agent",
    "cost_credits_agent": "src.adk_agents.cost_credits_agent.agent",
}

_FITFABRICA_AGENT_DEPLOY_CONFIGS = {
    "orchestrator_agent": ("src.adk_agents.orchestrator_agent.deploy_config", "OrchestratorAgentDeployConfig"),
    "user_profile_agent": ("src.adk_agents.user_profile_agent.deploy_config", "UserProfileAgentDeployConfig"),
    "business_profile_agent": ("src.adk_agents.business_profile_agent.deploy_config", "BusinessProfileAgentDeployConfig"),
    "human_identity_agent": ("src.adk_agents.human_identity_agent.deploy_config", "HumanIdentityAgentDeployConfig"),
    "garment_identity_agent": ("src.adk_agents.garment_identity_agent.deploy_config", "GarmentIdentityAgentDeployConfig"),
    "material_texture_agent": ("src.adk_agents.material_texture_agent.deploy_config", "MaterialTextureAgentDeployConfig"),
    "try_on_agent": ("src.adk_agents.try_on_agent.deploy_config", "TryOnAgentDeployConfig"),
    "quality_verifier_agent": ("src.adk_agents.quality_verifier_agent.deploy_config", "QualityVerifierAgentDeployConfig"),
    "repair_agent": ("src.adk_agents.repair_agent.deploy_config", "RepairAgentDeployConfig"),
    "fashion_stylist_agent": ("src.adk_agents.fashion_stylist_agent.deploy_config", "FashionStylistAgentDeployConfig"),
    "marketplace_agent": ("src.adk_agents.marketplace_agent.deploy_config", "MarketplaceAgentDeployConfig"),
    "trend_agent": ("src.adk_agents.trend_agent.deploy_config", "TrendAgentDeployConfig"),
    "pricing_agent": ("src.adk_agents.pricing_agent.deploy_config", "PricingAgentDeployConfig"),
    "product_card_agent": ("src.adk_agents.product_card_agent.deploy_config", "ProductCardAgentDeployConfig"),
    "cost_credits_agent": ("src.adk_agents.cost_credits_agent.deploy_config", "CostCreditsAgentDeployConfig"),
}


@dataclass(frozen=True)
class IdentityRuntimeRepositories:
    """Repository bundle used to construct runtime identity resolution services."""

    channel_identity_repo: object
    identity_binding_repo: object
    lead_repo: object


@dataclass(frozen=True)
class TryOnRuntimeDependencies:
    """Runtime bundle used to execute the portable Try-On workflow."""

    object_storage: object
    object_storage_root_prefix: str
    job_repository: TryOnJobRepositoryPort
    file_storage: TryOnFileStoragePort
    generation_adapter: TryOnGenerationPort
    human_identity_analyzer: HumanIdentityAnalysisPort
    garment_identity_analyzer: GarmentIdentityAnalysisPort
    material_texture_analyzer: MaterialTextureAnalysisPort
    analysis_bundle_service: TryOnAnalysisBundleService
    instruction_creator: TryOnInstructionPort
    quality_verifier: object
    repair_adapter: TryOnRepairPort | None
    stylist_adapter: object
    workflow_service: TryOnWorkflowService


@dataclass(frozen=True)
class SimilarSearchRuntimeDependencies:
    """Runtime bundle used to execute backend-owned similar search."""

    object_storage: object
    object_storage_root_prefix: str
    garment_identity_analyzer: object
    workflow_service: SimilarSearchWorkflowService
    click_event_service: SimilarSearchClickEventService


@dataclass(frozen=True)
class ProductCardRuntimeDependencies:
    """Runtime bundle used to execute backend-owned product-card workflows."""

    repository: object
    workflow_service: ProductCardWorkflowService


@dataclass(frozen=True)
class ContentPackageRuntimeDependencies:
    """Runtime bundle used to execute backend-owned content-package workflows."""

    repository: object
    workflow_service: ContentPackageWorkflowService


@dataclass(frozen=True)
class PricingRuntimeDependencies:
    """Runtime bundle used to execute backend-owned pricing workflows."""

    workflow_service: PricingWorkflowService


@dataclass(frozen=True)
class BillingRuntimeDependencies:
    """Runtime bundle used to execute backend-owned billing operations."""

    billing_service: BillingService


@dataclass(frozen=True)
class WorkspaceStateRuntimeDependencies:
    """Runtime bundle used to read persisted workspace state."""

    repository: WorkspaceStateRepositoryPort


@dataclass(frozen=True)
class OperationsRuntimeDependencies:
    """Runtime bundle used to execute portable queue and worker operations."""

    dispatch_service: WorkflowDispatchService
    worker_runtime: WorkerRuntime
    health_service: OperationsHealthService


@dataclass(frozen=True)
class BusinessCatalogSearchIndexingRuntimeDependencies:
    """Runtime bundle used to index approved B2B catalog records for search."""

    repository: object
    indexing_service: BusinessCatalogSearchIndexingService
    workflow_service: BusinessCatalogSearchIndexingWorkflow


@dataclass(frozen=True)
class FitFabricaAgentRuntimeDependencies:
    """Runtime bundle for approved FitFabrica product-agent roots and metadata."""

    provider_runtime: ProviderRuntime
    orchestrator_agent: BaseAgent
    orchestrator_deploy_config: OrchestratorAgentDeployConfig
    user_profile_agent: BaseAgent
    user_profile_deploy_config: UserProfileAgentDeployConfig
    business_profile_agent: BaseAgent
    business_profile_deploy_config: BusinessProfileAgentDeployConfig
    human_identity_agent: BaseAgent
    human_identity_deploy_config: HumanIdentityAgentDeployConfig
    garment_identity_agent: BaseAgent
    garment_identity_deploy_config: GarmentIdentityAgentDeployConfig
    material_texture_agent: BaseAgent
    material_texture_deploy_config: MaterialTextureAgentDeployConfig
    try_on_agent: BaseAgent
    try_on_deploy_config: TryOnAgentDeployConfig
    quality_verifier_agent: BaseAgent
    quality_verifier_deploy_config: QualityVerifierAgentDeployConfig
    repair_agent: BaseAgent
    repair_deploy_config: RepairAgentDeployConfig
    fashion_stylist_agent: BaseAgent
    fashion_stylist_deploy_config: FashionStylistAgentDeployConfig
    marketplace_agent: BaseAgent
    marketplace_deploy_config: MarketplaceAgentDeployConfig
    trend_agent: BaseAgent
    trend_deploy_config: TrendAgentDeployConfig
    pricing_agent: BaseAgent
    pricing_deploy_config: PricingAgentDeployConfig
    product_card_agent: BaseAgent
    product_card_deploy_config: ProductCardAgentDeployConfig
    cost_credits_agent: BaseAgent
    cost_credits_deploy_config: CostCreditsAgentDeployConfig


@dataclass(frozen=True)
class AgentInvocationRuntimeDependencies:
    """Runtime bundle for canonical backend-owned agent invocations."""

    gateway: AgentInvocationPort
    repository: AgentInvocationRepositoryPort
    invocation_service: AgentInvocationService


def load_fitfabrica_agent_root(module_name: str) -> object:
    """Load one FitFabrica ADK root agent only when the bundle is requested."""

    module = import_module(module_name)
    return getattr(module, "root_agent")


def load_fitfabrica_agent_deploy_config(module_name: str, class_name: str) -> object:
    """Load one FitFabrica deploy config only when the bundle is requested."""

    module = import_module(module_name)
    deploy_config_class = getattr(module, class_name)
    return deploy_config_class()


class NoOpVectorClient:
    """Fallback vector client that returns no hits when Qdrant is not configured."""

    def collection_exists(self, collection_name: str) -> bool:
        return True

    def create_collection(self, **kwargs) -> None:
        return None

    def search(self, **kwargs):
        return []

    def upsert(self, **kwargs) -> None:
        return None
