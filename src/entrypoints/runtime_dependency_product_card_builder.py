"""Product Card runtime composition isolated from other workflow builders."""

from __future__ import annotations

from src.adapters.agents.deterministic_garment_identity_analysis import DeterministicGarmentIdentityAnalysisAdapter
from src.adapters.agents.garment_identity_analysis import GarmentIdentityAnalysisAdapter
from src.adapters.agents.product_card_generation import ProductCardAgentGenerationAdapter
from src.adapters.database.sql.product_card_repositories import SqlProductCardRepository
from src.adapters.database.sql.garment_taxonomy_repositories import SqlGarmentTaxonomyRepository
from src.adapters.product_card.fake_generation import FakeProductCardGenerationAdapter
from src.adapters.product_card.file_storage import ProductCardObjectStorage
from src.adapters.product_card.in_memory_repository import InMemoryProductCardRepository
from src.domain.billing import BillingOwnerType
from src.entrypoints.runtime_dependency_contracts import ProductCardRuntimeDependencies
from src.entrypoints.runtime_dependency_foundation_builders import utc_now
from src.llm.agent_model_routing import resolve_agent_preferred_model
from src.use_cases.product_card.workflow_service import ProductCardWorkflowService
from src.use_cases.garment_taxonomy.service import GarmentTaxonomyService


def build_product_card_runtime_dependencies(
    settings,
    *,
    infrastructure,
    billing_service,
    billing_enabled: bool,
    agent_invocation_service,
) -> ProductCardRuntimeDependencies:
    """Build Product Card with a test-only fake or provider-neutral production agent."""
    object_storage_prefix = getattr(settings, "object_storage_prefix", "fitfabrica")
    repository = (
        SqlProductCardRepository(session_factory=infrastructure.sql_session_factory)
        if getattr(infrastructure, "sql_session_factory", None) is not None
        else InMemoryProductCardRepository()
    )
    is_test = str(getattr(settings, "environment", "")).strip().lower() == "test"
    generation_adapter = (
        FakeProductCardGenerationAdapter()
        if is_test
        else ProductCardAgentGenerationAdapter(
            invocation_service=agent_invocation_service,
            timeout_seconds=float(getattr(settings, "product_card_agent_timeout_seconds", 90.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="product_card_agent",
                task_kind="text_generation",
                risk_tier="low",
                explicit_model=getattr(settings, "product_card_agent_preferred_model", None),
            ),
        )
    )
    garment_identity_analyzer = (
        DeterministicGarmentIdentityAnalysisAdapter()
        if is_test
        else GarmentIdentityAnalysisAdapter(
            invocation_service=agent_invocation_service,
            object_storage=infrastructure.object_storage,
            minimum_confidence=float(getattr(settings, "garment_identity_agent_minimum_confidence", 0.75)),
            timeout_seconds=float(getattr(settings, "garment_identity_agent_timeout_seconds", 90.0)),
            preferred_model=resolve_agent_preferred_model(
                agent_name="garment_identity_agent",
                task_kind="visual_analysis",
                risk_tier="medium",
                explicit_model=getattr(settings, "garment_identity_agent_preferred_model", None),
            ),
            taxonomy_service=_build_garment_taxonomy_service(infrastructure),
        )
    )
    return ProductCardRuntimeDependencies(
        repository=repository,
        workflow_service=ProductCardWorkflowService(
            file_storage=ProductCardObjectStorage(
                object_storage=infrastructure.object_storage,
                tenant_id="public",
                root_prefix=object_storage_prefix,
            ),
            repository=repository,
            garment_identity_analyzer=garment_identity_analyzer,
            generation_adapter=generation_adapter,
            clock=utc_now,
            billing_service=billing_service if billing_enabled else None,
            billing_owner_id=getattr(settings, "default_person_credit_account_id", "public-person"),
            billing_owner_type=BillingOwnerType.PERSON,
        ),
    )


def _build_garment_taxonomy_service(infrastructure) -> GarmentTaxonomyService | None:
    """Build taxonomy service only when durable SQL storage is configured."""
    if getattr(infrastructure, "sql_session_factory", None) is None:
        return None
    return GarmentTaxonomyService(
        repository=SqlGarmentTaxonomyRepository(session_factory=infrastructure.sql_session_factory)
    )
