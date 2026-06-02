"""Composition root helpers for runtime service wiring."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.adk_agents.business_profile_agent.agent import root_agent as business_profile_root_agent
from src.adk_agents.business_profile_agent.deploy_config import BusinessProfileAgentDeployConfig
from src.adk_agents.fashion_stylist_agent.agent import root_agent as fashion_stylist_root_agent
from src.adk_agents.fashion_stylist_agent.deploy_config import FashionStylistAgentDeployConfig
from src.adk_agents.garment_identity_agent.agent import root_agent as garment_identity_root_agent
from src.adk_agents.garment_identity_agent.deploy_config import GarmentIdentityAgentDeployConfig
from src.adk_agents.human_identity_agent.agent import root_agent as human_identity_root_agent
from src.adk_agents.human_identity_agent.deploy_config import HumanIdentityAgentDeployConfig
from src.adk_agents.marketplace_agent.agent import root_agent as marketplace_root_agent
from src.adk_agents.marketplace_agent.deploy_config import MarketplaceAgentDeployConfig
from src.adk_agents.material_texture_agent.agent import root_agent as material_texture_root_agent
from src.adk_agents.material_texture_agent.deploy_config import MaterialTextureAgentDeployConfig
from src.adk_agents.orchestrator_agent.agent import root_agent as orchestrator_root_agent
from src.adk_agents.orchestrator_agent.deploy_config import OrchestratorAgentDeployConfig
from src.adk_agents.pricing_agent.agent import root_agent as pricing_root_agent
from src.adk_agents.pricing_agent.deploy_config import PricingAgentDeployConfig
from src.adk_agents.product_card_agent.agent import root_agent as product_card_root_agent
from src.adk_agents.product_card_agent.deploy_config import ProductCardAgentDeployConfig
from src.adk_agents.quality_verifier_agent.agent import root_agent as quality_verifier_root_agent
from src.adk_agents.quality_verifier_agent.deploy_config import QualityVerifierAgentDeployConfig
from src.adk_agents.repair_agent.agent import root_agent as repair_root_agent
from src.adk_agents.repair_agent.deploy_config import RepairAgentDeployConfig
from src.adk_agents.cost_credits_agent.agent import root_agent as cost_credits_root_agent
from src.adk_agents.cost_credits_agent.deploy_config import CostCreditsAgentDeployConfig
from src.adk_agents.trend_agent.agent import root_agent as trend_root_agent
from src.adk_agents.trend_agent.deploy_config import TrendAgentDeployConfig
from src.adk_agents.try_on_agent.agent import root_agent as try_on_root_agent
from src.adk_agents.try_on_agent.deploy_config import TryOnAgentDeployConfig
from src.adk_agents.user_profile_agent.agent import root_agent as user_profile_root_agent
from src.adk_agents.user_profile_agent.deploy_config import UserProfileAgentDeployConfig
from src.adapters.catalog import InMemoryCatalogRepository
from src.adapters.billing import InMemoryBillingRepository
from src.adapters.content_package.artifact_storage import ContentPackageArtifactStorage
from src.adapters.content_package.fake_generation import FakeContentPackageGenerationAdapter
from src.adapters.content_package.in_memory_repository import InMemoryContentPackageRepository
from src.adapters.operations import InMemoryOperationsRepository
from src.adapters.pricing.catalog_comparison_source import CatalogPricingComparisonSource
from src.adapters.pricing.in_memory_comparison_source import InMemoryPricingComparisonSource
from src.adapters.pricing.in_memory_repository import InMemoryPricingRepository
from src.adapters.product_card.fake_generation import FakeProductCardGenerationAdapter
from src.adapters.product_card.file_storage import ProductCardObjectStorage
from src.adapters.product_card.in_memory_repository import InMemoryProductCardRepository
from src.adapters.storage.media_storage import TryOnMediaStorage
from src.adapters.try_on import (
    DeterministicTryOnQualityVerifier,
    DeterministicTryOnRepairAdapter,
    DeterministicTryOnStylist,
    FallbackTryOnGenerationAdapter,
    FakeTryOnGenerationAdapter,
    ModelBackedTryOnQualityVerifier,
    ModelBackedTryOnStylist,
    ProviderRuntimeTryOnRepairAdapter,
    TryOnProviderGenerationAdapter,
    VertexVirtualTryOnGenerationAdapter,
)
from src.adapters.ai import VertexVirtualTryOnClient
from src.adapters.database.firestore.firestore_client_factory import get_firestore_client
from src.adapters.database.sql.catalog_repositories import SqlCatalogRepository
from src.adapters.database.sql.billing_repositories import SqlBillingRepository
from src.adapters.database.sql.identity_audit import SqlIdentityResolutionAuditRecorder
from src.adapters.database.sql.operations_repositories import SqlOperationsRepository
from src.adapters.database.sql.identity_repositories import (
    SqlChannelIdentityRepository,
    SqlIdentityBindingRepository,
    SqlLeadRepository,
)
from src.adapters.database.sql.try_on_repositories import SqlTryOnJobRepository
from src.adapters.database.sql.product_card_repositories import SqlProductCardRepository
from src.adapters.database.sql.content_package_repositories import SqlContentPackageRepository
from src.adapters.database.sql.pricing_repositories import SqlPricingRepository
from src.adapters.factories import get_messaging_adapter
from src.adapters.queue import InMemoryQueue, RedisQueue
from src.adapters.vector.qdrant_retriever import QdrantVectorRetriever
from src.identity_core.services.identity_core_runtime_repositories import (
    FirestoreChannelIdentityRepository,
    FirestoreIdentityBindingRepository,
    FirestoreLeadIdentityRepository,
    InMemoryChannelIdentityRepository,
    InMemoryIdentityBindingRepository,
    InMemoryLeadIdentityRepository,
)
from src.identity_core.services.identity_resolution import RuntimeIdentityResolutionService
from src.memory_layer import (
    FirestoreMemoryLayerRepository,
    InMemoryMemoryRunLedgerRepository,
    MemoryLayerService,
)
from src.memory_layer.run_ledger_repository import FirestoreMemoryRunLedgerRepository
from src.memory_layer.services.memory_run_ledger_service import MemoryRunLedgerService
from src.services.runtime.portable_infrastructure import build_portable_infrastructure
from src.llm.provider_runtime import ProviderRuntime, build_provider_runtime
from src.domain.billing import BillingOwnerType
from src.use_cases.billing import BillingPolicyResolver, BillingService
from src.use_cases.operations import OperationsHealthService, WorkerLeaseService, WorkflowDispatchService
from src.use_cases.try_on.ports import TryOnFileStoragePort, TryOnGenerationPort, TryOnJobRepositoryPort
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from src.use_cases.similar_search.workflow_service import SimilarSearchWorkflowService
from src.use_cases.product_card.workflow_service import ProductCardWorkflowService
from src.use_cases.content_package.workflow_service import ContentPackageWorkflowService
from src.use_cases.pricing.workflow_service import PricingWorkflowService
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.services.workers.worker_runtime import WorkerRuntime
from ..services.dialog.dialog_service import DialogService
from src.adapters.database.firestore.firestore_repositories import FirestoreLeadRepository, FirestoreSessionRepository
from src.memory_layer.services.memory_summary_service import MemorySummaryResult, MemorySummaryService
from ..services.rate_limit import create_rate_limiter

_CONTAINER_ATTR = "_runtime_container"
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
_FITFABRICA_AGENT_RUNTIME_ATTR = "_fitfabrica_agent_runtime_dependencies"


@dataclass(frozen=True)
class IdentityRuntimeRepositories:
    """Repository bundle used to construct runtime identity resolution services."""

    channel_identity_repo: object
    identity_binding_repo: object
    lead_repo: object


@dataclass(frozen=True)
class TryOnRuntimeDependencies:
    """Runtime bundle used to execute the portable Try-On workflow."""

    job_repository: TryOnJobRepositoryPort
    file_storage: TryOnFileStoragePort
    generation_adapter: TryOnGenerationPort
    quality_verifier: object
    repair_adapter: object
    stylist_adapter: object
    workflow_service: TryOnWorkflowService


@dataclass(frozen=True)
class SimilarSearchRuntimeDependencies:
    """Runtime bundle used to execute backend-owned similar search."""

    workflow_service: SimilarSearchWorkflowService


@dataclass(frozen=True)
class ProductCardRuntimeDependencies:
    """Runtime bundle used to execute backend-owned product-card workflows."""

    workflow_service: ProductCardWorkflowService


@dataclass(frozen=True)
class ContentPackageRuntimeDependencies:
    """Runtime bundle used to execute backend-owned content-package workflows."""

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
class OperationsRuntimeDependencies:
    """Runtime bundle used to execute portable queue and worker operations."""

    dispatch_service: WorkflowDispatchService
    worker_runtime: WorkerRuntime
    health_service: OperationsHealthService


@dataclass(frozen=True)
class FitFabricaAgentRuntimeDependencies:
    """Runtime bundle for approved FitFabrica product-agent roots and metadata."""

    provider_runtime: ProviderRuntime
    orchestrator_agent: Any
    orchestrator_deploy_config: OrchestratorAgentDeployConfig
    user_profile_agent: Any
    user_profile_deploy_config: UserProfileAgentDeployConfig
    business_profile_agent: Any
    business_profile_deploy_config: BusinessProfileAgentDeployConfig
    human_identity_agent: Any
    human_identity_deploy_config: HumanIdentityAgentDeployConfig
    garment_identity_agent: Any
    garment_identity_deploy_config: GarmentIdentityAgentDeployConfig
    material_texture_agent: Any
    material_texture_deploy_config: MaterialTextureAgentDeployConfig
    try_on_agent: Any
    try_on_deploy_config: TryOnAgentDeployConfig
    quality_verifier_agent: Any
    quality_verifier_deploy_config: QualityVerifierAgentDeployConfig
    repair_agent: Any
    repair_deploy_config: RepairAgentDeployConfig
    fashion_stylist_agent: Any
    fashion_stylist_deploy_config: FashionStylistAgentDeployConfig
    marketplace_agent: Any
    marketplace_deploy_config: MarketplaceAgentDeployConfig
    trend_agent: Any
    trend_deploy_config: TrendAgentDeployConfig
    pricing_agent: Any
    pricing_deploy_config: PricingAgentDeployConfig
    product_card_agent: Any
    product_card_deploy_config: ProductCardAgentDeployConfig
    cost_credits_agent: Any
    cost_credits_deploy_config: CostCreditsAgentDeployConfig


class RuntimeContainer:
    """Runtime-scoped dependency container with explicit lazy lifecycle."""

    def __init__(self, settings):
        self.settings = settings
        self._dialog_service: DialogService | None = None
        self._memory_summary_service: MemorySummaryService | None = None
        self._ingress_rate_limiter = None
        self._ingress_global_rate_limiter = None

    def _is_test_environment(self) -> bool:
        return str(getattr(self.settings, "environment", "")).strip().lower() == "test"

    def get_dialog_service(self) -> DialogService:
        if self._dialog_service is None:
            memory_layer_service = MemoryLayerService(
                repository=FirestoreMemoryLayerRepository(),
                settings=self.settings,
            )
            identity_resolution = RuntimeIdentityResolutionService(
                channel_identity_repo=identity_runtime_repositories(self.settings).channel_identity_repo,
                identity_binding_repo=identity_runtime_repositories(self.settings).identity_binding_repo,
                lead_repo=identity_runtime_repositories(self.settings).lead_repo,
                audit_recorder=identity_audit_recorder(self.settings),
            )
            if self._is_test_environment():
                rate_limiter = create_rate_limiter(self.settings, backend_override="inmemory")
            else:
                rate_limiter = create_rate_limiter(self.settings)
            self._dialog_service = DialogService(
                messaging=get_messaging_adapter(),
                leads_repo=FirestoreLeadRepository(memory_layer_service=memory_layer_service),
                sessions_repo=FirestoreSessionRepository(),
                settings=self.settings,
                rate_limiter=rate_limiter,
                identity_resolution_service=identity_resolution,
            )
        return self._dialog_service

    def get_memory_summary_service(self) -> MemorySummaryService:
        if self._memory_summary_service is None:
            memory_layer_service = MemoryLayerService(
                repository=FirestoreMemoryLayerRepository(),
                settings=self.settings,
            )
            if self._is_test_environment():
                run_ledger_service = MemoryRunLedgerService(repository=InMemoryMemoryRunLedgerRepository())
            else:
                run_ledger_service = MemoryRunLedgerService(repository=FirestoreMemoryRunLedgerRepository())
            self._memory_summary_service = MemorySummaryService(
                firestore=get_firestore_client(),
                settings=self.settings,
                leads_repo=FirestoreLeadRepository(memory_layer_service=memory_layer_service),
                memory_layer_service=memory_layer_service,
                memory_run_ledger_service=run_ledger_service,
            )
        return self._memory_summary_service

    def get_ingress_rate_limiter(self):
        if self._is_test_environment():
            return create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_rate_limit_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=self.settings.ingress_rate_limit_collection,
                backend_override="inmemory",
            )
        if self._ingress_rate_limiter is None:
            self._ingress_rate_limiter = create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_rate_limit_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=self.settings.ingress_rate_limit_collection,
            )
        return self._ingress_rate_limiter

    def get_ingress_global_safety_limiter(self):
        if self._is_test_environment():
            return create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_global_safety_cap_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=f"{self.settings.ingress_rate_limit_collection}_global",
                backend_override="inmemory",
            )
        if self._ingress_global_rate_limiter is None:
            self._ingress_global_rate_limiter = create_rate_limiter(
                self.settings,
                max_events=self.settings.ingress_global_safety_cap_max_events,
                window_seconds=self.settings.ingress_rate_limit_window_seconds,
                collection_name=f"{self.settings.ingress_rate_limit_collection}_global",
            )
        return self._ingress_global_rate_limiter


def runtime_container(settings) -> RuntimeContainer:
    container = getattr(settings, _CONTAINER_ATTR, None)
    if container is None:
        container = RuntimeContainer(settings)
        setattr(settings, _CONTAINER_ATTR, container)
    return container


def portable_infrastructure(settings):
    """Return the cached portable infrastructure bundle for the settings instance."""
    infrastructure = getattr(settings, _PORTABLE_INFRA_ATTR, None)
    if infrastructure is None:
        infrastructure = build_portable_infrastructure(settings)
        setattr(settings, _PORTABLE_INFRA_ATTR, infrastructure)
    return infrastructure


def identity_runtime_repositories(settings) -> IdentityRuntimeRepositories:
    """Return the runtime identity repository bundle for the current environment."""
    repositories = getattr(settings, _IDENTITY_RUNTIME_ATTR, None)
    if repositories is not None:
        return repositories

    infrastructure = portable_infrastructure(settings)
    if getattr(infrastructure, "sql_session_factory", None) is not None:
        repositories = IdentityRuntimeRepositories(
            channel_identity_repo=SqlChannelIdentityRepository(session_factory=infrastructure.sql_session_factory),
            identity_binding_repo=SqlIdentityBindingRepository(session_factory=infrastructure.sql_session_factory),
            lead_repo=SqlLeadRepository(session_factory=infrastructure.sql_session_factory),
        )
    elif str(getattr(settings, "environment", "")).strip().lower() == "test":
        repositories = IdentityRuntimeRepositories(
            channel_identity_repo=InMemoryChannelIdentityRepository(),
            identity_binding_repo=InMemoryIdentityBindingRepository(),
            lead_repo=InMemoryLeadIdentityRepository(),
        )
    else:
        repositories = IdentityRuntimeRepositories(
            channel_identity_repo=FirestoreChannelIdentityRepository(),
            identity_binding_repo=FirestoreIdentityBindingRepository(),
            lead_repo=FirestoreLeadIdentityRepository(),
        )

    setattr(settings, _IDENTITY_RUNTIME_ATTR, repositories)
    return repositories


def identity_audit_recorder(settings):
    """Return the runtime identity audit recorder when SQL infrastructure is configured."""
    recorder = getattr(settings, _IDENTITY_AUDIT_ATTR, None)
    if recorder is not None:
        return recorder

    infrastructure = portable_infrastructure(settings)
    recorder = (
        SqlIdentityResolutionAuditRecorder(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else None
    )
    setattr(settings, _IDENTITY_AUDIT_ATTR, recorder)
    return recorder


def provider_runtime(settings) -> ProviderRuntime:
    """Return the cached provider runtime bundle for the settings instance."""
    runtime = getattr(settings, _PROVIDER_RUNTIME_ATTR, None)
    if runtime is None:
        runtime = build_provider_runtime(settings)
        setattr(settings, _PROVIDER_RUNTIME_ATTR, runtime)
    return runtime


def _billing_enabled(settings) -> bool:
    """Return whether durable billing should be actively enforced for workflows."""
    return bool(getattr(settings, "billing_core_enabled", False))


def try_on_runtime_dependencies(settings) -> TryOnRuntimeDependencies:
    """Return the cached Try-On runtime bundle for the current settings instance."""
    runtime = getattr(settings, _TRY_ON_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    infrastructure = portable_infrastructure(settings)
    job_repository: TryOnJobRepositoryPort
    if getattr(infrastructure, "sql_session_factory", None) is not None:
        job_repository = SqlTryOnJobRepository(session_factory=infrastructure.sql_session_factory)
    else:
        job_repository = InMemoryTryOnJobRepository()

    file_storage = TryOnMediaStorage(
        object_storage=infrastructure.object_storage,
        tenant_id="public",
        root_prefix=settings.object_storage_prefix,
    )
    providers = provider_runtime(settings)
    try_on_generation_backend = getattr(settings, "try_on_generation_backend", "sandbox_fake")
    if try_on_generation_backend == "vertex_virtual_try_on":
        primary_generation_adapter = VertexVirtualTryOnGenerationAdapter(
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=settings.object_storage_prefix,
            signed_url_ttl_seconds=settings.object_storage_signed_url_ttl_seconds,
            vertex_client=VertexVirtualTryOnClient(
                project=settings.vertex_project or "",
                location=getattr(settings, "vertex_virtual_try_on_location", "global") or "global",
                model=getattr(settings, "vertex_virtual_try_on_model", "virtual-try-on-001"),
            ),
        )
        fallback_backend = getattr(settings, "try_on_vertex_failure_fallback_backend", "none")
        if fallback_backend == "provider_runtime":
            if providers.image_editing is None:
                raise RuntimeError(
                    "try_on_vertex_failure_fallback_backend=provider_runtime requires image_editing provider runtime"
                )
            generation_adapter = FallbackTryOnGenerationAdapter(
                primary=primary_generation_adapter,
                fallback=TryOnProviderGenerationAdapter(
                    image_editing_provider=providers.image_editing,
                    object_storage=infrastructure.object_storage,
                    tenant_id="public",
                    root_prefix=settings.object_storage_prefix,
                    signed_url_ttl_seconds=settings.object_storage_signed_url_ttl_seconds,
                ),
                fallback_backend_name="provider_runtime",
            )
        elif fallback_backend == "sandbox_fake":
            generation_adapter = FallbackTryOnGenerationAdapter(
                primary=primary_generation_adapter,
                fallback=FakeTryOnGenerationAdapter(),
                fallback_backend_name="sandbox_fake",
            )
        else:
            generation_adapter = primary_generation_adapter
    elif try_on_generation_backend == "provider_runtime" and providers.image_editing is not None:
        generation_adapter = TryOnProviderGenerationAdapter(
            image_editing_provider=providers.image_editing,
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=settings.object_storage_prefix,
            signed_url_ttl_seconds=settings.object_storage_signed_url_ttl_seconds,
        )
    else:
        generation_adapter = FakeTryOnGenerationAdapter()
    baseline_quality_verifier = DeterministicTryOnQualityVerifier(object_storage=infrastructure.object_storage)
    structured_reasoning_provider = getattr(providers, "structured_reasoning", None)
    if (
        getattr(settings, "try_on_quality_verifier_backend", "model_backed") == "model_backed"
        and structured_reasoning_provider is not None
    ):
        quality_verifier = ModelBackedTryOnQualityVerifier(
            baseline_verifier=baseline_quality_verifier,
            structured_reasoning_provider=structured_reasoning_provider,
        )
    else:
        quality_verifier = baseline_quality_verifier

    if (
        getattr(settings, "try_on_repair_backend", "provider_runtime") == "provider_runtime"
        and getattr(providers, "image_editing", None) is not None
    ):
        repair_adapter = ProviderRuntimeTryOnRepairAdapter(
            image_editing_provider=providers.image_editing,
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=settings.object_storage_prefix,
            signed_url_ttl_seconds=settings.object_storage_signed_url_ttl_seconds,
        )
    else:
        repair_adapter = DeterministicTryOnRepairAdapter(
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=settings.object_storage_prefix,
            signed_url_ttl_seconds=settings.object_storage_signed_url_ttl_seconds,
        )
    baseline_stylist = DeterministicTryOnStylist()
    if (
        getattr(settings, "try_on_stylist_backend", "model_backed") == "model_backed"
        and structured_reasoning_provider is not None
    ):
        stylist_adapter = ModelBackedTryOnStylist(
            structured_reasoning_provider=structured_reasoning_provider,
            fallback_stylist=baseline_stylist,
        )
    else:
        stylist_adapter = baseline_stylist

    workflow_service = TryOnWorkflowService(
        repository=job_repository,
        generator=generation_adapter,
        quality_verifier=quality_verifier,
        repair_adapter=repair_adapter,
        stylist_adapter=stylist_adapter,
        file_storage=file_storage,
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types=set(settings.try_on_allowed_content_types),
            max_upload_bytes=settings.try_on_max_upload_bytes,
        ),
        billing_service=billing_runtime_dependencies(settings).billing_service if _billing_enabled(settings) else None,
        billing_owner_id=getattr(settings, "default_person_credit_account_id", "public-person"),
        billing_owner_type=BillingOwnerType.PERSON,
    )
    runtime = TryOnRuntimeDependencies(
        job_repository=job_repository,
        file_storage=file_storage,
        generation_adapter=generation_adapter,
        quality_verifier=quality_verifier,
        repair_adapter=repair_adapter,
        stylist_adapter=stylist_adapter,
        workflow_service=workflow_service,
    )
    setattr(settings, _TRY_ON_RUNTIME_ATTR, runtime)
    return runtime


def similar_search_runtime_dependencies(settings) -> SimilarSearchRuntimeDependencies:
    """Return the cached similar-search runtime bundle for the current settings instance."""
    runtime = getattr(settings, _SIMILAR_SEARCH_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    infrastructure = portable_infrastructure(settings)
    providers = provider_runtime(settings)
    catalog_repository = (
        SqlCatalogRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryCatalogRepository()
    )
    vector_retriever = QdrantVectorRetriever(
        client=getattr(infrastructure, "qdrant_client", None) or _NoOpVectorClient(),
        collection_prefix=getattr(settings, "qdrant_collection_prefix", "fitfabrica"),
    )
    runtime = SimilarSearchRuntimeDependencies(
        workflow_service=SimilarSearchWorkflowService(
            embedding_provider=providers.embedding_provider,
            vector_retriever=vector_retriever,
            catalog_repository=catalog_repository,
        )
    )
    setattr(settings, _SIMILAR_SEARCH_RUNTIME_ATTR, runtime)
    return runtime


def product_card_runtime_dependencies(settings) -> ProductCardRuntimeDependencies:
    """Return the cached product-card runtime bundle for the current settings instance."""
    runtime = getattr(settings, _PRODUCT_CARD_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    infrastructure = portable_infrastructure(settings)
    repository = (
        SqlProductCardRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryProductCardRepository()
    )
    billing_service = billing_runtime_dependencies(settings).billing_service if _billing_enabled(settings) else None
    runtime = ProductCardRuntimeDependencies(
        workflow_service=ProductCardWorkflowService(
            file_storage=ProductCardObjectStorage(
                object_storage=infrastructure.object_storage,
                tenant_id="public",
                root_prefix=settings.object_storage_prefix,
            ),
            repository=repository,
            generation_adapter=FakeProductCardGenerationAdapter(),
            clock=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            billing_service=billing_service,
            billing_owner_id=getattr(settings, "default_business_credit_account_id", "public-business"),
        )
    )
    setattr(settings, _PRODUCT_CARD_RUNTIME_ATTR, runtime)
    return runtime


def content_package_runtime_dependencies(settings) -> ContentPackageRuntimeDependencies:
    """Return the cached content-package runtime bundle for the current settings instance."""
    runtime = getattr(settings, _CONTENT_PACKAGE_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    infrastructure = portable_infrastructure(settings)
    repository = (
        SqlContentPackageRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryContentPackageRepository()
    )
    billing_service = billing_runtime_dependencies(settings).billing_service if _billing_enabled(settings) else None
    runtime = ContentPackageRuntimeDependencies(
        workflow_service=ContentPackageWorkflowService(
            repository=repository,
            artifact_storage=ContentPackageArtifactStorage(
                object_storage=infrastructure.object_storage,
                tenant_id="public",
                root_prefix=settings.object_storage_prefix,
            ),
            generation_adapter=FakeContentPackageGenerationAdapter(),
            clock=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            billing_service=billing_service,
            billing_owner_id=getattr(settings, "default_business_credit_account_id", "public-business"),
        )
    )
    setattr(settings, _CONTENT_PACKAGE_RUNTIME_ATTR, runtime)
    return runtime


def pricing_runtime_dependencies(settings) -> PricingRuntimeDependencies:
    """Return the cached pricing runtime bundle for the current settings instance."""
    runtime = getattr(settings, _PRICING_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    infrastructure = portable_infrastructure(settings)
    if getattr(infrastructure, "sql_session_factory", None) is not None:
        repository = SqlPricingRepository(session_factory=infrastructure.sql_session_factory)
        comparison_source = CatalogPricingComparisonSource(
            catalog_repository=SqlCatalogRepository(session_factory=infrastructure.sql_session_factory)
        )
    else:
        repository = InMemoryPricingRepository()
        comparison_source = InMemoryPricingComparisonSource()
    billing_service = billing_runtime_dependencies(settings).billing_service if _billing_enabled(settings) else None
    runtime = PricingRuntimeDependencies(
        workflow_service=PricingWorkflowService(
            repository=repository,
            comparison_source=comparison_source,
            clock=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
            billing_service=billing_service,
            billing_owner_id=getattr(settings, "default_business_credit_account_id", "public-business"),
        )
    )
    setattr(settings, _PRICING_RUNTIME_ATTR, runtime)
    return runtime


def billing_runtime_dependencies(settings) -> BillingRuntimeDependencies:
    """Return the cached billing runtime bundle for the current settings instance."""
    runtime = getattr(settings, _BILLING_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    infrastructure = portable_infrastructure(settings)
    repository = (
        SqlBillingRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryBillingRepository()
    )
    runtime = BillingRuntimeDependencies(
        billing_service=BillingService(
            repository=repository,
            policy_resolver=BillingPolicyResolver(
                workflow_base_costs={
                    "try_on": int(getattr(settings, "try_on_base_credit_cost", 12)),
                    "product_card": int(getattr(settings, "product_card_base_credit_cost", 18)),
                    "content_package": int(getattr(settings, "content_package_base_credit_cost", 14)),
                    "pricing": int(getattr(settings, "pricing_base_credit_cost", 6)),
                }
            ),
        )
    )
    setattr(settings, _BILLING_RUNTIME_ATTR, runtime)
    return runtime


def operations_runtime_dependencies(settings) -> OperationsRuntimeDependencies:
    """Return the cached operations runtime bundle for the current settings instance."""
    runtime = getattr(settings, _OPERATIONS_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    infrastructure = portable_infrastructure(settings)
    repository = (
        SqlOperationsRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryOperationsRepository()
    )
    queue_backend = getattr(settings, "operations_queue_backend", "in_memory")
    if queue_backend == "redis" and getattr(infrastructure, "redis_client", None) is not None:
        queue = RedisQueue(
            redis_client=infrastructure.redis_client,
            queue_name=getattr(settings, "operations_queue_name", "fitfabrica:workflow-queue"),
        )
        resolved_backend = "redis"
    else:
        queue = InMemoryQueue()
        resolved_backend = "in_memory"
    lease_service = WorkerLeaseService(
        repository=repository,
        clock=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        lease_duration_seconds=getattr(settings, "processing_lease_duration_seconds", 300),
    )
    worker_name = getattr(settings, "operations_worker_name", "portable-worker")
    handlers = {
        "try_on": lambda job: try_on_runtime_dependencies(settings).workflow_service.execute_job(
            job_id=job.workflow_reference,
            lifecycle_mode=job.payload.get("sandbox_lifecycle_mode", "complete"),
        ),
        "product_card": lambda job: product_card_runtime_dependencies(settings).workflow_service.execute_product_card_job(
            job_id=job.workflow_reference
        ),
        "content_package": lambda job: content_package_runtime_dependencies(settings).workflow_service.execute_content_package_job(
            job_id=job.workflow_reference
        ),
        "pricing": lambda job: pricing_runtime_dependencies(settings).workflow_service.execute_pricing_job(
            job_id=job.workflow_reference
        ),
    }
    runtime = OperationsRuntimeDependencies(
        dispatch_service=WorkflowDispatchService(
            repository=repository,
            queue=queue,
            clock=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        ),
        worker_runtime=WorkerRuntime(
            queue=queue,
            repository=repository,
            lease_service=lease_service,
            handlers=handlers,
            worker_name=worker_name,
            clock=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        ),
        health_service=OperationsHealthService(
            repository=repository,
            queue_backend=resolved_backend,
            worker_name=worker_name,
            postgres_configured=bool(getattr(settings, "postgres_dsn", None)),
            redis_configured=bool(getattr(settings, "redis_url", None)),
        ),
    )
    setattr(settings, _OPERATIONS_RUNTIME_ATTR, runtime)
    return runtime


def fitfabrica_agent_runtime_dependencies(settings) -> FitFabricaAgentRuntimeDependencies:
    """Return the cached FitFabrica product-agent runtime bundle."""
    runtime = getattr(settings, _FITFABRICA_AGENT_RUNTIME_ATTR, None)
    if runtime is not None:
        return runtime

    runtime = FitFabricaAgentRuntimeDependencies(
        provider_runtime=provider_runtime(settings),
        orchestrator_agent=orchestrator_root_agent,
        orchestrator_deploy_config=OrchestratorAgentDeployConfig(),
        user_profile_agent=user_profile_root_agent,
        user_profile_deploy_config=UserProfileAgentDeployConfig(),
        business_profile_agent=business_profile_root_agent,
        business_profile_deploy_config=BusinessProfileAgentDeployConfig(),
        human_identity_agent=human_identity_root_agent,
        human_identity_deploy_config=HumanIdentityAgentDeployConfig(),
        garment_identity_agent=garment_identity_root_agent,
        garment_identity_deploy_config=GarmentIdentityAgentDeployConfig(),
        material_texture_agent=material_texture_root_agent,
        material_texture_deploy_config=MaterialTextureAgentDeployConfig(),
        try_on_agent=try_on_root_agent,
        try_on_deploy_config=TryOnAgentDeployConfig(),
        quality_verifier_agent=quality_verifier_root_agent,
        quality_verifier_deploy_config=QualityVerifierAgentDeployConfig(),
        repair_agent=repair_root_agent,
        repair_deploy_config=RepairAgentDeployConfig(),
        fashion_stylist_agent=fashion_stylist_root_agent,
        fashion_stylist_deploy_config=FashionStylistAgentDeployConfig(),
        marketplace_agent=marketplace_root_agent,
        marketplace_deploy_config=MarketplaceAgentDeployConfig(),
        trend_agent=trend_root_agent,
        trend_deploy_config=TrendAgentDeployConfig(),
        pricing_agent=pricing_root_agent,
        pricing_deploy_config=PricingAgentDeployConfig(),
        product_card_agent=product_card_root_agent,
        product_card_deploy_config=ProductCardAgentDeployConfig(),
        cost_credits_agent=cost_credits_root_agent,
        cost_credits_deploy_config=CostCreditsAgentDeployConfig(),
    )
    setattr(settings, _FITFABRICA_AGENT_RUNTIME_ATTR, runtime)
    return runtime


class _NoOpVectorClient:
    """Fallback vector client that returns no hits when Qdrant is not configured."""

    def search(self, **kwargs):
        return []

    def upsert(self, **kwargs) -> None:
        return None


def dialog_service(settings) -> DialogService:
    return runtime_container(settings).get_dialog_service()


def memory_summary_service(settings) -> MemorySummaryService:
    return runtime_container(settings).get_memory_summary_service()


def ingress_rate_limiter(settings):
    return runtime_container(settings).get_ingress_rate_limiter()


def ingress_global_safety_limiter(settings):
    return runtime_container(settings).get_ingress_global_safety_limiter()


def safe_memory_summary_response(*, result: MemorySummaryResult) -> dict[str, object]:
    """Build a sanitized task/cron response without runtime diagnostic leakage."""
    pipeline_status = "failed" if result.outcome_counts.get("failed", 0) > 0 else "completed"
    return {
        "pipeline_status": pipeline_status,
        "date": result.date.isoformat(),
        "leads_processed": result.leads_processed,
        "summaries_written": result.summaries_written,
        "error_count": result.error_count,
        "has_errors": result.error_count > 0,
        "outcomes": dict(result.outcome_counts),
        "reason_codes": dict(result.reason_code_counts),
    }
