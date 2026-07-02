"""Workflow and operations runtime builders."""
from __future__ import annotations

from src.adapters.billing import InMemoryBillingRepository
from src.adapters.business_catalog import (
    BusinessCatalogObjectStorage,
    InMemoryBusinessCatalogRepository,
    SandboxBusinessCatalogCategoryAnalyzer,
)
from src.adapters.business_catalog.category_analysis import GarmentIdentityBusinessCatalogCategoryAnalyzer
from src.adapters.agents.human_identity_analysis import HumanIdentityAnalysisAdapter
from src.adapters.agents.garment_identity_analysis import GarmentIdentityAnalysisAdapter
from src.adapters.agents.deterministic_garment_identity_analysis import DeterministicGarmentIdentityAnalysisAdapter
from src.adapters.agents.deterministic_human_identity_analysis import DeterministicHumanIdentityAnalysisAdapter
from src.adapters.agents.deterministic_try_on_garment_identity_analysis import DeterministicTryOnGarmentIdentityAnalysisAdapter
from src.adapters.agents.deterministic_try_on_material_texture_analysis import DeterministicTryOnMaterialTextureAnalysisAdapter
from src.adapters.agents.try_on_garment_identity_analysis import TryOnGarmentIdentityAnalysisAdapter
from src.adapters.agents.try_on_material_texture_analysis import TryOnMaterialTextureAnalysisAdapter
from src.adapters.agents.try_on_instruction import TryOnInstructionAgentAdapter
from src.adapters.agents.deterministic_try_on_instruction import DeterministicTryOnInstructionAdapter
from src.adapters.content_package.artifact_storage import ContentPackageArtifactStorage
from src.adapters.content_package.fake_generation import FakeContentPackageGenerationAdapter
from src.adapters.content_package.in_memory_repository import InMemoryContentPackageRepository
from src.adapters.database.sql.billing_repositories import SqlBillingRepository
from src.adapters.database.sql.business_catalog_repositories import SqlBusinessCatalogRepository
from src.adapters.database.sql.catalog_repositories import SqlCatalogRepository
from src.adapters.database.sql.content_package_repositories import SqlContentPackageRepository
from src.adapters.database.sql.garment_taxonomy_repositories import SqlGarmentTaxonomyRepository
from src.adapters.database.sql.pricing_repositories import SqlPricingRepository
from src.adapters.database.sql.similar_search_repositories import SqlSimilarSearchClickEventRepository
from src.adapters.database.sql.try_on_repositories import SqlTryOnJobRepository
from src.adapters.pricing.catalog_comparison_source import CatalogPricingComparisonSource
from src.adapters.pricing.in_memory_comparison_source import InMemoryPricingComparisonSource
from src.adapters.pricing.in_memory_repository import InMemoryPricingRepository
from src.adapters.storage.media_storage import TryOnMediaStorage
from src.adapters.similar_search import InMemorySimilarSearchClickEventRepository
from src.adapters.try_on.deterministic_quality_verifier import DeterministicTryOnQualityVerifier
from src.adapters.try_on.deterministic_repair_adapter import DeterministicTryOnRepairAdapter
from src.adapters.try_on.deterministic_stylist import DeterministicTryOnStylist
from src.adapters.try_on.fallback_generation import FallbackTryOnGenerationAdapter
from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.adapters.try_on.model_backed_stylist import ModelBackedTryOnStylist
from src.adapters.try_on.provider_generation import TryOnProviderGenerationAdapter
from src.adapters.try_on.provider_repair_adapter import ProviderRuntimeTryOnRepairAdapter
from src.adapters.try_on.quality_verifier_agent_adapter import TryOnQualityVerifierAgentAdapter
from src.adapters.try_on.repair_agent_planner import TryOnRepairAgentPlanner
from src.adapters.vector.qdrant_bootstrapper import QdrantVectorBootstrapper
from src.adapters.vector.qdrant_retriever import QdrantVectorRetriever
from src.domain.billing import BillingOwnerType
from src.entrypoints.runtime_dependency_contracts import (
    BillingRuntimeDependencies,
    BusinessCatalogSearchIndexingRuntimeDependencies,
    ContentPackageRuntimeDependencies,
    NoOpVectorClient,
    PricingRuntimeDependencies,
    SimilarSearchRuntimeDependencies,
    TryOnRuntimeDependencies,
)
from src.entrypoints.runtime_dependency_foundation_builders import utc_now
from src.llm.agent_model_routing import resolve_agent_preferred_model
from src.use_cases.billing import BillingPolicyResolver, BillingService
from src.use_cases.business_catalog.idempotency import InMemoryBusinessCatalogIdempotencyStore
from src.use_cases.business_catalog.search_indexing import BusinessCatalogSearchIndexingService
from src.use_cases.business_catalog.search_indexing_workflow import BusinessCatalogSearchIndexingWorkflow
from src.use_cases.business_catalog.service import BusinessCatalogService
from src.use_cases.content_package.workflow_service import ContentPackageWorkflowService
from src.use_cases.pricing.workflow_service import PricingWorkflowService
from src.use_cases.similar_search.workflow_service import SimilarSearchWorkflowService
from src.use_cases.similar_search.events import SimilarSearchClickEventService
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService
from src.use_cases.try_on.human_identity_policy import HumanIdentityContinuationPolicy
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundleService
from src.use_cases.garment_taxonomy.service import GarmentTaxonomyService


_NON_PRODUCTION_IMAGE_EDITING_PROVIDERS = frozenset({"", "stub_image_editing"})


def _is_production_image_editing_provider(provider: object | None) -> bool:
    """Return whether the image-editing provider can be used on real paid outputs."""

    if provider is None:
        return False
    provider_name = str(getattr(provider, "provider_name", "")).strip().lower()
    return provider_name not in _NON_PRODUCTION_IMAGE_EDITING_PROVIDERS


def build_try_on_runtime_dependencies(
    settings,
    *,
    infrastructure,
    providers,
    billing_service,
    billing_enabled: bool,
    vertex_virtual_try_on_client_factory,
    agent_invocation_service,
) -> TryOnRuntimeDependencies:
    """Build the Try-On runtime bundle for the current settings instance."""

    if getattr(infrastructure, "sql_session_factory", None) is not None:
        job_repository = SqlTryOnJobRepository(session_factory=infrastructure.sql_session_factory)
    else:
        job_repository = InMemoryTryOnJobRepository()
    object_storage_prefix = getattr(settings, "object_storage_prefix", "fitfabrica")
    signed_url_ttl_seconds = getattr(settings, "object_storage_signed_url_ttl_seconds", 900)
    try_on_allowed_content_types = getattr(settings, "try_on_allowed_content_types", ["image/jpeg", "image/png", "image/webp"])
    try_on_max_upload_bytes = getattr(settings, "try_on_max_upload_bytes", 10 * 1024 * 1024)
    file_storage = TryOnMediaStorage(object_storage=infrastructure.object_storage, tenant_id="public", root_prefix=object_storage_prefix)
    try_on_generation_backend = getattr(settings, "try_on_generation_backend", "sandbox_fake")
    if try_on_generation_backend == "vertex_virtual_try_on":
        from src.adapters.try_on.vertex_virtual_try_on_generation import VertexVirtualTryOnGenerationAdapter

        primary_generation_adapter = VertexVirtualTryOnGenerationAdapter(
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=object_storage_prefix,
            signed_url_ttl_seconds=signed_url_ttl_seconds,
            vertex_client=vertex_virtual_try_on_client_factory(
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
                    root_prefix=object_storage_prefix,
                    signed_url_ttl_seconds=signed_url_ttl_seconds,
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
            root_prefix=object_storage_prefix,
            signed_url_ttl_seconds=signed_url_ttl_seconds,
        )
    else:
        generation_adapter = FakeTryOnGenerationAdapter()
    baseline_quality_verifier = DeterministicTryOnQualityVerifier(object_storage=infrastructure.object_storage)
    structured_reasoning_provider = getattr(providers, "structured_reasoning", None)
    quality_verifier = (
        TryOnQualityVerifierAgentAdapter(
            baseline_verifier=baseline_quality_verifier,
            object_storage=infrastructure.object_storage,
            invocation_service=agent_invocation_service,
            timeout_seconds=float(getattr(settings, "try_on_quality_verifier_timeout_seconds", 120.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="quality_verifier_agent",
                task_kind="visual_quality_verification",
                risk_tier="high",
                explicit_model=getattr(settings, "try_on_quality_verifier_preferred_model", None),
            ),
        )
        if getattr(settings, "try_on_quality_verifier_backend", "model_backed") == "model_backed"
        and agent_invocation_service is not None
        else baseline_quality_verifier
    )
    repair_backend = getattr(settings, "try_on_repair_backend", "provider_runtime")
    image_editing_provider = getattr(providers, "image_editing", None)
    real_vertex_generation = try_on_generation_backend == "vertex_virtual_try_on"
    if real_vertex_generation and not _is_production_image_editing_provider(image_editing_provider):
        repair_adapter = None
    elif real_vertex_generation and repair_backend == "deterministic":
        repair_adapter = None
    elif repair_backend == "provider_runtime" and image_editing_provider is not None:
        repair_instruction_planner = (
            TryOnRepairAgentPlanner(
                object_storage=infrastructure.object_storage,
                invocation_service=agent_invocation_service,
                timeout_seconds=float(getattr(settings, "try_on_repair_agent_timeout_seconds", 90.0)),
                preferred_model=resolve_agent_preferred_model(
                    agent_name="repair_agent",
                    task_kind="repair_instruction",
                    risk_tier="medium",
                    explicit_model=getattr(settings, "try_on_repair_agent_preferred_model", None),
                ),
            )
            if agent_invocation_service is not None
            else None
        )
        repair_adapter = ProviderRuntimeTryOnRepairAdapter(
            image_editing_provider=image_editing_provider,
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=object_storage_prefix,
            signed_url_ttl_seconds=signed_url_ttl_seconds,
            repair_instruction_planner=repair_instruction_planner,
        )
    else:
        repair_adapter = DeterministicTryOnRepairAdapter(
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=object_storage_prefix,
            signed_url_ttl_seconds=signed_url_ttl_seconds,
        )
    baseline_stylist = DeterministicTryOnStylist()
    stylist_adapter = (
        ModelBackedTryOnStylist(structured_reasoning_provider=structured_reasoning_provider, fallback_stylist=baseline_stylist)
        if getattr(settings, "try_on_stylist_backend", "model_backed") == "model_backed"
        and structured_reasoning_provider is not None
        else baseline_stylist
    )
    human_identity_analyzer = (
        DeterministicHumanIdentityAnalysisAdapter()
        if str(getattr(settings, "environment", "")).strip().lower() == "test"
        else HumanIdentityAnalysisAdapter(
            invocation_service=agent_invocation_service,
            policy=HumanIdentityContinuationPolicy(
                minimum_confidence=float(getattr(settings, "try_on_human_identity_minimum_confidence", 0.8))
            ),
            timeout_seconds=float(getattr(settings, "try_on_human_identity_timeout_seconds", 60.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="human_identity_agent",
                task_kind="visual_analysis",
                risk_tier="high",
                explicit_model=getattr(settings, "try_on_human_identity_preferred_model", None),
            ),
        )
    )
    if str(getattr(settings, "environment", "")).strip().lower() == "test":
        garment_identity_analyzer = DeterministicTryOnGarmentIdentityAnalysisAdapter()
        material_texture_analyzer = DeterministicTryOnMaterialTextureAnalysisAdapter()
        instruction_creator = DeterministicTryOnInstructionAdapter()
    else:
        garment_taxonomy_service = _build_garment_taxonomy_service(infrastructure)
        garment_identity_analyzer = TryOnGarmentIdentityAnalysisAdapter(
            invocation_service=agent_invocation_service,
            minimum_confidence=float(getattr(settings, "try_on_garment_identity_minimum_confidence", 0.75)),
            timeout_seconds=float(getattr(settings, "try_on_garment_identity_timeout_seconds", 90.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="garment_identity_agent",
                task_kind="visual_analysis",
                risk_tier="medium",
                explicit_model=getattr(settings, "try_on_garment_identity_preferred_model", None),
            ),
            taxonomy_service=garment_taxonomy_service,
        )
        material_texture_analyzer = TryOnMaterialTextureAnalysisAdapter(
            invocation_service=agent_invocation_service,
            minimum_confidence=float(getattr(settings, "try_on_material_texture_minimum_confidence", 0.7)),
            timeout_seconds=float(getattr(settings, "try_on_material_texture_timeout_seconds", 90.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="material_texture_agent",
                task_kind="visual_analysis",
                risk_tier="medium",
                explicit_model=getattr(settings, "try_on_material_texture_preferred_model", None),
            ),
        )
        instruction_creator = TryOnInstructionAgentAdapter(
            invocation_service=agent_invocation_service,
            minimum_confidence=float(getattr(settings, "try_on_instruction_minimum_confidence", 0.8)),
            timeout_seconds=float(getattr(settings, "try_on_instruction_timeout_seconds", 60.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="try_on_agent",
                task_kind="text_generation",
                risk_tier="medium",
                explicit_model=getattr(settings, "try_on_instruction_preferred_model", None),
            ),
        )
    analysis_bundle_service = TryOnAnalysisBundleService(
        human_identity_analyzer=human_identity_analyzer,
        garment_identity_analyzer=garment_identity_analyzer,
        material_texture_analyzer=material_texture_analyzer,
    )
    workflow_service = TryOnWorkflowService(
        repository=job_repository,
        generator=generation_adapter,
        analysis_bundle_service=analysis_bundle_service,
        instruction_creator=instruction_creator,
        quality_verifier=quality_verifier,
        repair_adapter=repair_adapter,
        stylist_adapter=stylist_adapter,
        file_storage=file_storage,
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types=set(try_on_allowed_content_types),
            max_upload_bytes=try_on_max_upload_bytes,
        ),
        billing_service=billing_service if billing_enabled else None,
        billing_owner_id=getattr(settings, "default_person_credit_account_id", "public-person"),
        billing_owner_type=BillingOwnerType.PERSON,
    )
    return TryOnRuntimeDependencies(
        object_storage=infrastructure.object_storage,
        object_storage_root_prefix=object_storage_prefix,
        job_repository=job_repository,
        file_storage=file_storage,
        generation_adapter=generation_adapter,
        human_identity_analyzer=human_identity_analyzer,
        garment_identity_analyzer=garment_identity_analyzer,
        material_texture_analyzer=material_texture_analyzer,
        analysis_bundle_service=analysis_bundle_service,
        instruction_creator=instruction_creator,
        quality_verifier=quality_verifier,
        repair_adapter=repair_adapter,
        stylist_adapter=stylist_adapter,
        workflow_service=workflow_service,
    )


def build_similar_search_runtime_dependencies(settings, *, infrastructure, providers, agent_invocation_service=None) -> SimilarSearchRuntimeDependencies:
    object_storage_prefix = getattr(settings, "object_storage_prefix", "fitfabrica")
    event_repository = (
        SqlSimilarSearchClickEventRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemorySimilarSearchClickEventRepository()
    )
    business_catalog_repository = (
        SqlBusinessCatalogRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryBusinessCatalogRepository()
    )
    vector_retriever = QdrantVectorRetriever(
        client=getattr(infrastructure, "qdrant_client", None) or NoOpVectorClient(),
        collection_prefix=getattr(settings, "qdrant_collection_prefix", "fitfabrica"),
    )
    if str(getattr(settings, "environment", "")).strip().lower() == "test" or agent_invocation_service is None:
        garment_identity_analyzer = DeterministicGarmentIdentityAnalysisAdapter()
    else:
        garment_identity_analyzer = GarmentIdentityAnalysisAdapter(
            invocation_service=agent_invocation_service,
            object_storage=infrastructure.object_storage,
            minimum_confidence=float(getattr(settings, "similar_search_garment_identity_minimum_confidence", 0.75)),
            timeout_seconds=float(getattr(settings, "similar_search_garment_identity_timeout_seconds", 90.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="garment_identity_agent",
                task_kind="visual_analysis",
                risk_tier="medium",
                explicit_model=getattr(settings, "similar_search_garment_identity_preferred_model", None),
            ),
            taxonomy_service=_build_garment_taxonomy_service(infrastructure),
        )
    return SimilarSearchRuntimeDependencies(
        object_storage=infrastructure.object_storage,
        object_storage_root_prefix=object_storage_prefix,
        garment_identity_analyzer=garment_identity_analyzer,
        workflow_service=SimilarSearchWorkflowService(
            embedding_provider=providers.embedding_provider,
            vector_retriever=vector_retriever,
            catalog_repository=business_catalog_repository,
            local_catalog_search=business_catalog_repository,
        ),
        click_event_service=SimilarSearchClickEventService(repository=event_repository),
    )


def build_content_package_runtime_dependencies(settings, *, infrastructure, billing_service, billing_enabled: bool) -> ContentPackageRuntimeDependencies:
    object_storage_prefix = getattr(settings, "object_storage_prefix", "fitfabrica")
    repository = (
        SqlContentPackageRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryContentPackageRepository()
    )
    return ContentPackageRuntimeDependencies(
        repository=repository,
        workflow_service=ContentPackageWorkflowService(
            repository=repository,
            artifact_storage=ContentPackageArtifactStorage(object_storage=infrastructure.object_storage, tenant_id="public", root_prefix=object_storage_prefix),
            generation_adapter=FakeContentPackageGenerationAdapter(),
            clock=utc_now,
            billing_service=billing_service if billing_enabled else None,
            billing_owner_id=getattr(settings, "default_business_credit_account_id", "public-business"),
        ),
    )


def build_pricing_runtime_dependencies(settings, *, infrastructure, billing_service, billing_enabled: bool) -> PricingRuntimeDependencies:
    if getattr(infrastructure, "sql_session_factory", None) is not None:
        repository = SqlPricingRepository(session_factory=infrastructure.sql_session_factory)
        comparison_source = CatalogPricingComparisonSource(
            catalog_repository=SqlCatalogRepository(session_factory=infrastructure.sql_session_factory)
        )
    else:
        repository = InMemoryPricingRepository()
        comparison_source = InMemoryPricingComparisonSource()
    return PricingRuntimeDependencies(
        workflow_service=PricingWorkflowService(
            repository=repository,
            comparison_source=comparison_source,
            clock=utc_now,
            billing_service=billing_service if billing_enabled else None,
            billing_owner_id=getattr(settings, "default_business_credit_account_id", "public-business"),
        )
    )


def build_billing_runtime_dependencies(settings, *, infrastructure) -> BillingRuntimeDependencies:
    repository = (
        SqlBillingRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryBillingRepository()
    )
    return BillingRuntimeDependencies(
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


def build_business_catalog_service(settings, *, infrastructure, agent_invocation_service=None) -> BusinessCatalogService:
    """Build the backend-owned B2B catalog service for business/admin routes."""

    repository = (
        SqlBusinessCatalogRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryBusinessCatalogRepository()
    )
    object_storage_prefix = getattr(settings, "object_storage_prefix", "fitfabrica")
    validation_mode = str(getattr(settings, "business_catalog_category_validation_mode", "agent")).strip().lower()
    if validation_mode == "sandbox":
        category_analyzer = SandboxBusinessCatalogCategoryAnalyzer()
    elif str(getattr(settings, "environment", "")).strip().lower() == "test" or agent_invocation_service is None:
        garment_identity_analyzer = DeterministicGarmentIdentityAnalysisAdapter()
        category_analyzer = GarmentIdentityBusinessCatalogCategoryAnalyzer(
            garment_identity_analyzer=garment_identity_analyzer
        )
    else:
        garment_identity_analyzer = GarmentIdentityAnalysisAdapter(
            invocation_service=agent_invocation_service,
            object_storage=infrastructure.object_storage,
            minimum_confidence=float(getattr(settings, "business_catalog_category_validation_minimum_confidence", 0.75)),
            timeout_seconds=float(getattr(settings, "business_catalog_category_validation_timeout_seconds", 90.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="garment_identity_agent",
                task_kind="visual_analysis",
                risk_tier="medium",
                explicit_model=getattr(settings, "business_catalog_category_validation_preferred_model", None),
            ),
            taxonomy_service=_build_garment_taxonomy_service(infrastructure),
        )
        category_analyzer = GarmentIdentityBusinessCatalogCategoryAnalyzer(
            garment_identity_analyzer=garment_identity_analyzer
        )
    return BusinessCatalogService(
        repository=repository,
        file_storage=BusinessCatalogObjectStorage(
            object_storage=infrastructure.object_storage,
            tenant_id="public",
            root_prefix=object_storage_prefix,
        ),
        category_analyzer=category_analyzer,
        idempotency_store=InMemoryBusinessCatalogIdempotencyStore(),
    )


def build_business_catalog_search_indexing_runtime_dependencies(
    settings,
    *,
    infrastructure,
    providers,
) -> BusinessCatalogSearchIndexingRuntimeDependencies:
    """Build the backend-owned B2B catalog search indexing runtime."""

    repository = (
        SqlBusinessCatalogRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryBusinessCatalogRepository()
    )
    qdrant_client = getattr(infrastructure, "qdrant_client", None) or NoOpVectorClient()
    collection_prefix = getattr(settings, "qdrant_collection_prefix", "fitfabrica")
    indexing_service = BusinessCatalogSearchIndexingService(
        embedding_provider=providers.embedding_provider,
        vector_index=QdrantVectorRetriever(
            client=qdrant_client,
            collection_prefix=collection_prefix,
        ),
        vector_bootstrapper=QdrantVectorBootstrapper(
            client=qdrant_client,
            collection_prefix=collection_prefix,
        ),
    )
    return BusinessCatalogSearchIndexingRuntimeDependencies(
        repository=repository,
        indexing_service=indexing_service,
        workflow_service=BusinessCatalogSearchIndexingWorkflow(
            repository=repository,
            indexing_service=indexing_service,
        ),
    )


def _build_garment_taxonomy_service(infrastructure) -> GarmentTaxonomyService | None:
    """Build taxonomy service only when durable SQL storage is configured."""
    if getattr(infrastructure, "sql_session_factory", None) is None:
        return None
    return GarmentTaxonomyService(
        repository=SqlGarmentTaxonomyRepository(session_factory=infrastructure.sql_session_factory)
    )
