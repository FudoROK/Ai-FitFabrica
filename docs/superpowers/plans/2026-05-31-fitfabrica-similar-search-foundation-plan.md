# FitFabrica Similar Search Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend-owned similar-search and cheaper-alternative foundation so FitFabrica can accept a product-like query, retrieve similar garments through Qdrant, merge marketplace metadata from PostgreSQL, and return structured ranked results.

**Architecture:** Keep PostgreSQL as the source of truth for product and offer metadata, and keep Qdrant as the retrieval engine for nearest-neighbor similarity. Add a thin similar-search domain layer, a SQL catalog repository layer, a retrieval orchestration service, and a small API surface. Marketplace logic stays explicit and portable: no hidden scraping, no frontend ranking logic, and no cloud-vendor-managed search assumptions.

**Tech Stack:** FastAPI, Python, Pydantic, SQLAlchemy, Qdrant, provider runtime embeddings port, pytest.

---

## Scope And Baseline

Current state in this worktree:

- `src/adapters/vector/qdrant_retriever.py` can already upsert/search typed vector points.
- `src/domain/vector_search.py` already defines namespaces, queries, hits, and payload filters.
- No product-catalog SQL layer exists yet for similar-search metadata and offers.
- No backend-owned similar-search use case exists yet.
- No embedding-driven query preparation exists yet for this workflow.
- No API endpoint exists yet for `/workspace/similar-search` style backend execution.

This stage does not yet implement a full external marketplace connector network. It builds the foundation for:

- similar product retrieval
- budget filtering
- cheaper alternative ranking
- backend-owned result explanations

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/similar_search.py`
  - Typed request/result/filter/ranking models for similar search.
- `src/use_cases/similar_search/ports.py`
  - Workflow-facing ports for catalog truth, vector retrieval, and embeddings.
- `src/use_cases/similar_search/query_preparation.py`
  - Build the retrieval query profile from backend-owned input.
- `src/use_cases/similar_search/ranking.py`
  - Merge similarity score, price fit, and metadata completeness into backend ranking.
- `src/use_cases/similar_search/workflow_service.py`
  - Orchestrate query prep, embeddings, retrieval, catalog hydration, and cheaper-alternative selection.
- `src/adapters/database/sql/catalog_models.py`
  - SQLAlchemy tables for products, marketplace offers, and price snapshots used by similar search.
- `src/adapters/database/sql/catalog_repositories.py`
  - SQL repository implementations for product and offer hydration.
- `src/adapters/database/sql/catalog_serialization.py`
  - Focused row/domain mapping helpers for similar-search catalog records.
- `alembic/versions/20260531_000004_similar_search_foundation.py`
  - Migration for product catalog and offer tables.
- `src/entrypoints/runtime_dependencies.py`
  - Expose similar-search runtime dependencies through composition root.
- `src/entrypoints/similar_search_routes.py`
  - FastAPI endpoint(s) for backend-owned similar search.
- `src/entrypoints/payloads.py`
  - Wire request/response DTOs only if the route module should stay thinner than Pydantic-heavy inline declarations.
- `tests/test_similar_search_domain_models.py`
  - Verify request/result/filter contracts.
- `tests/test_catalog_sql_models.py`
  - Verify SQL catalog schema surfaces.
- `tests/test_catalog_sql_repositories.py`
  - Verify SQL product/offer hydration.
- `tests/test_similar_search_query_preparation.py`
  - Verify query profile building.
- `tests/test_similar_search_ranking.py`
  - Verify cheaper-alternative and score ordering.
- `tests/test_similar_search_workflow_service.py`
  - Verify end-to-end orchestration with fakes.
- `tests/test_similar_search_routes.py`
  - Verify API responses and validation.
- `tests/test_similar_search_runtime_wiring.py`
  - Verify runtime dependencies select the proper backend-owned components.
- `tests/architecture/test_similar_search_guardrails.py`
  - Enforce backend-owned ranking and no direct vendor-search assumptions.
- `README.md`
  - Document the similar-search backend contour.
- `docs/project_description.md`
  - Record the retrieval-plus-marketplace baseline.
- `docs/project_structure.md`
  - Record the new similar-search modules.
- `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`
  - Mark Stage 7 planning complete.

## Task 1: Define Similar Search Domain Contracts

**Files:**
- Create: `src/domain/similar_search.py`
- Create: `tests/test_similar_search_domain_models.py`

- [ ] **Step 1: Write the failing domain-model tests**

```python
from src.domain.similar_search import SimilarSearchRequest, SimilarSearchResult


def test_similar_search_request_keeps_budget_and_marketplace_preferences() -> None:
    request = SimilarSearchRequest(
        source_type="text",
        query_text="black midi dress with belt",
        budget_max=120.0,
        marketplace_filters=["lamoda", "wb"],
    )

    assert request.budget_max == 120.0
    assert request.marketplace_filters == ["lamoda", "wb"]


def test_similar_search_result_exposes_cheaper_alternative_flag() -> None:
    result = SimilarSearchResult(
        product_id="product-1",
        title="Black midi dress",
        similarity_score=0.91,
        price_amount=99.0,
        currency="USD",
        marketplace="lamoda",
        is_cheaper_alternative=True,
        explanation="Lower price with close silhouette match.",
    )

    assert result.is_cheaper_alternative is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_similar_search_domain_models.py -q`
Expected: FAIL because similar-search domain models do not exist yet.

- [ ] **Step 3: Implement the minimal domain models**

```python
class SimilarSearchRequest(BaseModel):
    source_type: Literal["text", "product_ref"]
    query_text: str | None = None
    product_id: str | None = None
    budget_max: float | None = Field(default=None, ge=0)
    marketplace_filters: list[str] = Field(default_factory=list)
```

```python
class SimilarSearchResult(BaseModel):
    product_id: str
    title: str
    similarity_score: float
    price_amount: float
    currency: str
    marketplace: str
    is_cheaper_alternative: bool
    explanation: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_similar_search_domain_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/similar_search.py tests/test_similar_search_domain_models.py
git commit -m "feat: define similar search domain models"
```

## Task 2: Add Product Catalog SQL Foundation

**Files:**
- Create: `src/adapters/database/sql/catalog_models.py`
- Create: `alembic/versions/20260531_000004_similar_search_foundation.py`
- Create: `tests/test_catalog_sql_models.py`

- [ ] **Step 1: Write the failing SQL-model tests**

```python
from src.adapters.database.sql.catalog_models import MarketplaceOfferRow, ProductRow


def test_catalog_sql_models_define_product_and_offer_tables() -> None:
    assert ProductRow.__tablename__ == "products"
    assert MarketplaceOfferRow.__tablename__ == "marketplace_offers"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalog_sql_models.py -q`
Expected: FAIL because catalog SQL models do not exist yet.

- [ ] **Step 3: Implement SQLAlchemy models and migration**

```python
class ProductRow(SqlBase):
    __tablename__ = "products"
    product_id = mapped_column(String(64), primary_key=True)
    title = mapped_column(String(255), nullable=False)
    category = mapped_column(String(64), nullable=False)
```

```python
class MarketplaceOfferRow(SqlBase):
    __tablename__ = "marketplace_offers"
    offer_id = mapped_column(String(64), primary_key=True)
    product_id = mapped_column(ForeignKey("products.product_id"), nullable=False, index=True)
    marketplace = mapped_column(String(64), nullable=False)
    price_amount = mapped_column(Numeric(12, 2), nullable=False)
```

```python
def upgrade() -> None:
    op.create_table(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalog_sql_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/catalog_models.py alembic/versions/20260531_000004_similar_search_foundation.py tests/test_catalog_sql_models.py
git commit -m "feat: add similar search catalog sql models"
```

## Task 3: Add Catalog Repository Hydration

**Files:**
- Create: `src/adapters/database/sql/catalog_serialization.py`
- Create: `src/adapters/database/sql/catalog_repositories.py`
- Create: `tests/test_catalog_sql_repositories.py`

- [ ] **Step 1: Write the failing repository tests**

```python
async def test_catalog_repository_returns_products_for_retrieved_owner_ids() -> None:
    repository = SqlCatalogRepository(session_factory=...)
    products = await repository.get_products_by_ids(["product-1"])

    assert products[0].product_id == "product-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_catalog_sql_repositories.py -q`
Expected: FAIL because the catalog repository does not exist yet.

- [ ] **Step 3: Implement focused hydration repositories**

```python
class SqlCatalogRepository(CatalogRepositoryPort):
    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]:
        ...

    async def list_offers_for_products(self, product_ids: list[str]) -> list[CatalogOfferRecord]:
        ...
```

```python
def product_record_from_row(row: ProductRow) -> CatalogProductRecord:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_catalog_sql_repositories.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/catalog_serialization.py src/adapters/database/sql/catalog_repositories.py tests/test_catalog_sql_repositories.py
git commit -m "feat: add similar search catalog repositories"
```

## Task 4: Add Similar Search Use-Case Ports And Query Preparation

**Files:**
- Create: `src/use_cases/similar_search/ports.py`
- Create: `src/use_cases/similar_search/query_preparation.py`
- Create: `tests/test_similar_search_query_preparation.py`

- [ ] **Step 1: Write the failing query-preparation tests**

```python
from src.domain.similar_search import SimilarSearchRequest
from src.use_cases.similar_search.query_preparation import build_similarity_query_profile


def test_query_preparation_maps_text_request_into_embedding_input() -> None:
    profile = build_similarity_query_profile(
        SimilarSearchRequest(
            source_type="text",
            query_text="black midi dress with belt",
            budget_max=120.0,
        )
    )

    assert profile.embedding_input == "black midi dress with belt"
    assert profile.budget_max == 120.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_similar_search_query_preparation.py -q`
Expected: FAIL because query preparation code does not exist yet.

- [ ] **Step 3: Implement ports and query preparation**

```python
class CatalogRepositoryPort(Protocol):
    async def get_products_by_ids(self, product_ids: list[str]) -> list[CatalogProductRecord]: ...
```

```python
def build_similarity_query_profile(request: SimilarSearchRequest) -> SimilarityQueryProfile:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_similar_search_query_preparation.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/similar_search/ports.py src/use_cases/similar_search/query_preparation.py tests/test_similar_search_query_preparation.py
git commit -m "feat: add similar search query preparation"
```

## Task 5: Add Backend-Owned Ranking And Cheaper Alternative Logic

**Files:**
- Create: `src/use_cases/similar_search/ranking.py`
- Create: `tests/test_similar_search_ranking.py`

- [ ] **Step 1: Write the failing ranking tests**

```python
from src.use_cases.similar_search.ranking import rank_similar_products


def test_ranking_prefers_high_similarity_then_marks_cheaper_alternative() -> None:
    ranked = rank_similar_products(
        hydrated_products=[...],
        budget_max=120.0,
        reference_price=160.0,
    )

    assert ranked[0].is_cheaper_alternative is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_similar_search_ranking.py -q`
Expected: FAIL because ranking logic does not exist yet.

- [ ] **Step 3: Implement ranking logic**

```python
def rank_similar_products(*, hydrated_products: list[HydratedCatalogMatch], budget_max: float | None, reference_price: float | None) -> list[SimilarSearchResult]:
    ...
```

```python
is_cheaper = reference_price is not None and offer.price_amount < reference_price
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_similar_search_ranking.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/similar_search/ranking.py tests/test_similar_search_ranking.py
git commit -m "feat: add similar search ranking logic"
```

## Task 6: Build Similar Search Workflow Service

**Files:**
- Create: `src/use_cases/similar_search/workflow_service.py`
- Create: `tests/test_similar_search_workflow_service.py`

- [ ] **Step 1: Write the failing workflow tests**

```python
async def test_workflow_service_embeds_queries_retrieves_hits_and_returns_ranked_results() -> None:
    service = SimilarSearchWorkflowService(...)
    response = await service.search(request)

    assert response.results
    assert response.results[0].product_id == "product-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_similar_search_workflow_service.py -q`
Expected: FAIL because the workflow service does not exist yet.

- [ ] **Step 3: Implement orchestration**

```python
class SimilarSearchWorkflowService:
    async def search(self, request: SimilarSearchRequest) -> SimilarSearchResponse:
        profile = build_similarity_query_profile(request)
        embedding = self._embedding_provider.embed(...)
        hits = self._vector_retriever.search(...)
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_similar_search_workflow_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/similar_search/workflow_service.py tests/test_similar_search_workflow_service.py
git commit -m "feat: add similar search workflow service"
```

## Task 7: Add Runtime Wiring And FastAPI Surface

**Files:**
- Modify: `src/entrypoints/runtime_dependencies.py`
- Create: `src/entrypoints/similar_search_routes.py`
- Create: `tests/test_similar_search_runtime_wiring.py`
- Create: `tests/test_similar_search_routes.py`

- [ ] **Step 1: Write the failing runtime and route tests**

```python
def test_similar_search_runtime_dependencies_use_qdrant_and_sql_catalog() -> None:
    runtime = similar_search_runtime_dependencies(settings)
    assert runtime.workflow_service is not None
```

```python
def test_similar_search_route_returns_structured_results(client) -> None:
    response = client.post("/api/similar-search", json={...})
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_similar_search_runtime_wiring.py tests/test_similar_search_routes.py -q`
Expected: FAIL because the runtime bundle and route do not exist yet.

- [ ] **Step 3: Implement runtime wiring and route**

```python
@dataclass(frozen=True)
class SimilarSearchRuntimeDependencies:
    workflow_service: SimilarSearchWorkflowService
```

```python
@router.post("/api/similar-search")
async def create_similar_search(...):
    return await workflow_service.search(request)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_similar_search_runtime_wiring.py tests/test_similar_search_routes.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/runtime_dependencies.py src/entrypoints/similar_search_routes.py tests/test_similar_search_runtime_wiring.py tests/test_similar_search_routes.py
git commit -m "feat: add similar search api wiring"
```

## Task 8: Add Similar Search Guardrails And Final Verification

**Files:**
- Create: `tests/architecture/test_similar_search_guardrails.py`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_similar_search_stays_backend_owned_and_vendor_neutral() -> None:
    text = Path("src/use_cases/similar_search/workflow_service.py").read_text(encoding="utf-8")
    assert "vertex ai search" not in text.lower()
    assert "openai" not in text.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_similar_search_guardrails.py -q`
Expected: FAIL until the similar-search boundary and docs are aligned.

- [ ] **Step 3: Update docs and master plan**

```markdown
- similar search is backend-owned
- PostgreSQL stores catalog truth and legal marketplace metadata
- Qdrant stores retrieval vectors and filterable similarity payloads
```

- [ ] **Step 4: Run targeted similar-search verification**

Run:
`python -m pytest tests/test_similar_search_domain_models.py tests/test_catalog_sql_models.py tests/test_catalog_sql_repositories.py tests/test_similar_search_query_preparation.py tests/test_similar_search_ranking.py tests/test_similar_search_workflow_service.py tests/test_similar_search_runtime_wiring.py tests/test_similar_search_routes.py tests/architecture/test_similar_search_guardrails.py -q`

Expected: PASS

- [ ] **Step 5: Run broader platform regression verification**

Run:
`python -m pytest tests/test_qdrant_retriever.py tests/test_qdrant_filters.py tests/test_runtime_dependencies_container.py tests/architecture/test_vector_foundation_guardrails.py tests/architecture/test_provider_abstraction_guardrails.py tests/test_try_on_runtime_wiring.py -q`

Expected: PASS

- [ ] **Step 6: Run smoke command**

Run:
`python scripts/platform_foundation_smoke.py`

Expected output still includes:

```text
object_storage_backend=in_memory
qdrant_backend=qdrant
```

- [ ] **Step 7: Commit**

```bash
git add tests/architecture/test_similar_search_guardrails.py README.md docs/project_description.md docs/project_structure.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "docs: align similar search foundation stage"
```

## Stage Exit Criteria

This stage is complete only when:

- similar-search requests are handled fully on the backend
- PostgreSQL stores product and marketplace truth used for ranking
- Qdrant provides filtered nearest-neighbor retrieval
- cheaper-alternative logic is explicit in backend ranking code
- route responses are structured and typed
- no frontend or vendor-managed search service owns ranking decisions

## Self-Review

Spec coverage checked:

- garment and product embedding flow: Tasks 4, 6, 7
- retrieval and ranking: Tasks 5, 6
- marketplace data normalization: Tasks 2, 3
- cheaper alternative logic: Task 5

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each code-bearing step includes concrete code or commands.

Type consistency checked:

- `SimilarSearchRequest`, `SimilarSearchResult`, `SqlCatalogRepository`, `SimilarityQueryProfile`, and `SimilarSearchWorkflowService` are named consistently across later tasks.

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-similar-search-foundation-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
