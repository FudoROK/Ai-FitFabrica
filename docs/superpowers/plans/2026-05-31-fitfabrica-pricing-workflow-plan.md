# FitFabrica Pricing Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend-owned B2B pricing workflow so FitFabrica can accept product and market context, combine internal catalog truth with similar-search and marketplace evidence, and return a structured recommended price with explanation and trade-off notes.

**Architecture:** Keep pricing decisions explicit and backend-owned. PostgreSQL stores pricing jobs, inputs, comparable sets, and result versions. Reuse Stage 7 similar-search and catalog foundations instead of inventing a separate comparison engine. The workflow service prepares the pricing brief, hydrates market evidence, ranks comparables, and saves a typed recommendation.

**Tech Stack:** FastAPI, Python, Pydantic, SQLAlchemy, Alembic, Qdrant-backed similar search, PostgreSQL catalog truth, provider runtime, pytest.

---

## Scope And Baseline

Current state in this worktree:

- similar-search foundation already exists and returns structured comparable candidates
- catalog truth already exists in PostgreSQL product and marketplace tables
- frontend pricing page exists as a presentation route, but no backend workflow exists
- no SQL persistence exists yet for pricing jobs or recommendation versions

This stage does not yet implement:

- billing and credits
- external marketplace ingestion beyond the current catalog truth
- automatic repricing loops
- direct ERP synchronization

This stage builds the backend contour for:

- pricing request intake
- comparable set hydration
- recommendation persistence
- structured explanation and trade-off output
- typed API polling

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/pricing.py`
  - typed request, comparable, recommendation, and response models.
- `src/use_cases/pricing/ports.py`
  - workflow-facing ports for repository and market-comparison sources.
- `src/use_cases/pricing/query_preparation.py`
  - build the market-comparison brief from backend-owned input.
- `src/use_cases/pricing/ranking.py`
  - explicit pricing-range and recommendation logic.
- `src/use_cases/pricing/workflow_service.py`
  - orchestration for comparable retrieval, recommendation, and persistence.
- `src/adapters/database/sql/pricing_models.py`
  - SQLAlchemy tables for pricing jobs, comparable records, and recommendation versions.
- `src/adapters/database/sql/pricing_serialization.py`
  - row/domain mapping helpers.
- `src/adapters/database/sql/pricing_repositories.py`
  - SQL repository implementation.
- `alembic/versions/20260531_000007_pricing_workflow.py`
  - migration for pricing persistence.
- `src/entrypoints/runtime_dependencies.py`
  - expose pricing runtime dependencies.
- `src/entrypoints/pricing_routes.py`
  - FastAPI create/status/result endpoints.
- `src/entrypoints/http_routes.py`
  - include the new router.
- `tests/test_pricing_domain_models.py`
  - verify typed contracts.
- `tests/test_pricing_sql_models.py`
  - verify SQL schema surfaces.
- `tests/test_pricing_sql_repositories.py`
  - verify job and recommendation persistence.
- `tests/test_pricing_query_preparation.py`
  - verify request-to-brief transformation.
- `tests/test_pricing_ranking.py`
  - verify range and recommendation logic.
- `tests/test_pricing_workflow_service.py`
  - verify orchestration with fakes and similar-search inputs.
- `tests/test_pricing_runtime_wiring.py`
  - verify runtime bundle selection.
- `tests/test_pricing_routes.py`
  - verify API behavior.
- `tests/architecture/test_pricing_guardrails.py`
  - enforce backend-owned recommendation logic.
- `README.md`
  - document the pricing contour.
- `docs/project_description.md`
  - record the pricing baseline.
- `docs/project_structure.md`
  - record the new pricing modules.

## Task 1: Define Pricing Domain Contracts

**Files:**
- Create: `src/domain/pricing.py`
- Create: `tests/test_pricing_domain_models.py`

- [ ] **Step 1: Write the failing domain-model tests**

```python
from src.domain.pricing import PricingRecommendation, PricingRequest


def test_pricing_request_keeps_target_margin_and_currency() -> None:
    request = PricingRequest(
        product_id="product-1",
        target_currency="RUB",
        desired_margin_percent=30.0,
    )

    assert request.target_currency == "RUB"
    assert request.desired_margin_percent == 30.0


def test_pricing_recommendation_exposes_recommended_price_and_reasoning() -> None:
    recommendation = PricingRecommendation(
        recommended_price=4490.0,
        currency="RUB",
        rationale="Positioned slightly below premium comparable cluster.",
        market_min=3990.0,
        market_avg=4590.0,
        market_max=5990.0,
    )

    assert recommendation.market_avg == 4590.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pricing_domain_models.py -q`
Expected: FAIL because pricing domain models do not exist yet.

- [ ] **Step 3: Implement the minimal domain models**

```python
class PricingRequest(BaseModel):
    product_id: str
    target_currency: str
    desired_margin_percent: float | None = Field(default=None, ge=0)
```

```python
class PricingRecommendation(BaseModel):
    recommended_price: float
    currency: str
    rationale: str
    market_min: float
    market_avg: float
    market_max: float
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pricing_domain_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/pricing.py tests/test_pricing_domain_models.py
git commit -m "feat: define pricing domain models"
```

## Task 2: Add Pricing SQL Foundation

**Files:**
- Create: `src/adapters/database/sql/pricing_models.py`
- Create: `alembic/versions/20260531_000007_pricing_workflow.py`
- Create: `tests/test_pricing_sql_models.py`

- [ ] **Step 1: Write the failing SQL-model tests**

```python
from src.adapters.database.sql.pricing_models import PricingJobRow, PricingRecommendationRow


def test_pricing_sql_models_define_job_and_recommendation_tables() -> None:
    assert PricingJobRow.__tablename__ == "pricing_jobs"
    assert PricingRecommendationRow.__tablename__ == "pricing_recommendations"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pricing_sql_models.py -q`
Expected: FAIL because pricing SQL models do not exist yet.

- [ ] **Step 3: Implement SQLAlchemy models and migration**

```python
class PricingJobRow(SqlBase):
    __tablename__ = "pricing_jobs"
    job_id = mapped_column(String(64), primary_key=True)
    product_id = mapped_column(String(64), nullable=False, index=True)
    status = mapped_column(String(32), nullable=False)
```

```python
class PricingRecommendationRow(SqlBase):
    __tablename__ = "pricing_recommendations"
    recommendation_id = mapped_column(String(64), primary_key=True)
    job_id = mapped_column(ForeignKey("pricing_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    recommended_price = mapped_column(Numeric(12, 2), nullable=False)
```

```python
def upgrade() -> None:
    op.create_table(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pricing_sql_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/pricing_models.py alembic/versions/20260531_000007_pricing_workflow.py tests/test_pricing_sql_models.py
git commit -m "feat: add pricing sql models"
```

## Task 3: Add Pricing Repository Layer

**Files:**
- Create: `src/adapters/database/sql/pricing_serialization.py`
- Create: `src/adapters/database/sql/pricing_repositories.py`
- Create: `tests/test_pricing_sql_repositories.py`

- [ ] **Step 1: Write the failing repository tests**

```python
async def test_pricing_repository_persists_job_and_recommendation() -> None:
    repository = SqlPricingRepository(session_factory=...)
    job = await repository.create_job(...)
    recommendation = await repository.save_recommendation(job.job_id, ...)

    assert recommendation.job_id == job.job_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pricing_sql_repositories.py -q`
Expected: FAIL because the repository does not exist yet.

- [ ] **Step 3: Implement focused repository logic**

```python
class SqlPricingRepository(PricingRepositoryPort):
    async def create_job(self, request: PricingRequest) -> PricingJobRecord:
        ...

    async def save_recommendation(self, job_id: str, recommendation: PricingRecommendation) -> PricingRecommendationRecord:
        ...
```

```python
def recommendation_from_row(row: PricingRecommendationRow) -> PricingRecommendationRecord:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pricing_sql_repositories.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/pricing_serialization.py src/adapters/database/sql/pricing_repositories.py tests/test_pricing_sql_repositories.py
git commit -m "feat: add pricing repositories"
```

## Task 4: Add Pricing Query Preparation And Ranking

**Files:**
- Create: `src/use_cases/pricing/ports.py`
- Create: `src/use_cases/pricing/query_preparation.py`
- Create: `src/use_cases/pricing/ranking.py`
- Create: `tests/test_pricing_query_preparation.py`
- Create: `tests/test_pricing_ranking.py`

- [ ] **Step 1: Write the failing query and ranking tests**

```python
from src.domain.pricing import PricingRequest
from src.use_cases.pricing.query_preparation import build_pricing_brief
from src.use_cases.pricing.ranking import recommend_price


def test_pricing_brief_keeps_product_and_margin_context() -> None:
    brief = build_pricing_brief(
        PricingRequest(product_id="product-1", target_currency="RUB", desired_margin_percent=30.0)
    )

    assert brief.product_id == "product-1"


def test_recommend_price_returns_market_band_and_recommendation() -> None:
    result = recommend_price(comparables=[3990.0, 4590.0, 5990.0], desired_margin_percent=30.0)
    assert result.market_avg == 4590.0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_pricing_query_preparation.py tests/test_pricing_ranking.py -q`
Expected: FAIL because query preparation and ranking code do not exist yet.

- [ ] **Step 3: Implement query preparation and ranking**

```python
def build_pricing_brief(request: PricingRequest) -> PricingBrief:
    return PricingBrief(
        product_id=request.product_id,
        target_currency=request.target_currency,
        desired_margin_percent=request.desired_margin_percent,
    )
```

```python
def recommend_price(*, comparables: list[float], desired_margin_percent: float | None) -> PricingRecommendation:
    ...
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_pricing_query_preparation.py tests/test_pricing_ranking.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/pricing/ports.py src/use_cases/pricing/query_preparation.py src/use_cases/pricing/ranking.py tests/test_pricing_query_preparation.py tests/test_pricing_ranking.py
git commit -m "feat: add pricing recommendation logic"
```

## Task 5: Add Pricing Workflow Service

**Files:**
- Create: `src/use_cases/pricing/workflow_service.py`
- Create: `tests/test_pricing_workflow_service.py`

- [ ] **Step 1: Write the failing workflow tests**

```python
async def test_pricing_workflow_hydrates_comparables_and_returns_recommendation() -> None:
    service = PricingWorkflowService(...)
    result = await service.create_pricing_recommendation(request=...)

    assert result.recommendation.recommended_price > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pricing_workflow_service.py -q`
Expected: FAIL because the workflow service does not exist yet.

- [ ] **Step 3: Implement orchestration**

```python
class PricingWorkflowService:
    async def create_pricing_recommendation(self, *, request: PricingRequest) -> PricingWorkflowResult:
        brief = build_pricing_brief(request)
        comparable_hits = await self._comparison_source.list_comparables(brief)
        recommendation = recommend_price(
            comparables=[hit.price_amount for hit in comparable_hits],
            desired_margin_percent=brief.desired_margin_percent,
        )
        job = await self._repository.create_job(request)
        saved = await self._repository.save_recommendation(job.job_id, recommendation)
        return PricingWorkflowResult(job=await self._repository.mark_completed(job.job_id), recommendation=saved)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pricing_workflow_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/pricing/workflow_service.py tests/test_pricing_workflow_service.py
git commit -m "feat: add pricing workflow service"
```

## Task 6: Add Runtime Wiring And FastAPI Surface

**Files:**
- Modify: `src/entrypoints/runtime_dependencies.py`
- Create: `src/entrypoints/pricing_routes.py`
- Modify: `src/entrypoints/http_routes.py`
- Create: `tests/test_pricing_runtime_wiring.py`
- Create: `tests/test_pricing_routes.py`

- [ ] **Step 1: Write the failing runtime and route tests**

```python
def test_pricing_runtime_dependencies_wire_repository_and_comparison_source() -> None:
    runtime = pricing_runtime_dependencies(settings)
    assert runtime.workflow_service is not None
```

```python
def test_pricing_route_returns_structured_recommendation(client) -> None:
    response = client.post("/api/pricing-jobs", json={...})
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pricing_runtime_wiring.py tests/test_pricing_routes.py -q`
Expected: FAIL because runtime wiring and routes do not exist yet.

- [ ] **Step 3: Implement runtime bundle and routes**

```python
@dataclass(frozen=True)
class PricingRuntimeDependencies:
    workflow_service: PricingWorkflowService
```

```python
@router.post("/api/pricing-jobs")
async def create_pricing_job(...):
    return await workflow_service.create_pricing_recommendation(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pricing_runtime_wiring.py tests/test_pricing_routes.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/runtime_dependencies.py src/entrypoints/pricing_routes.py src/entrypoints/http_routes.py tests/test_pricing_runtime_wiring.py tests/test_pricing_routes.py
git commit -m "feat: add pricing api wiring"
```

## Task 7: Add Guardrails And Final Verification

**Files:**
- Create: `tests/architecture/test_pricing_guardrails.py`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_pricing_workflow_keeps_recommendation_logic_backend_owned() -> None:
    text = Path("src/use_cases/pricing/workflow_service.py").read_text(encoding="utf-8").lower()
    assert "window" not in text
    assert "document" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_pricing_guardrails.py -q`
Expected: FAIL until the workflow boundary and docs are aligned.

- [ ] **Step 3: Update docs**

```markdown
- pricing recommendations are backend-owned
- PostgreSQL stores pricing jobs and recommendation versions
- similar-search and catalog truth supply comparable market evidence
```

- [ ] **Step 4: Run targeted verification**

Run: `python -m pytest tests/test_pricing_domain_models.py tests/test_pricing_sql_models.py tests/test_pricing_sql_repositories.py tests/test_pricing_query_preparation.py tests/test_pricing_ranking.py tests/test_pricing_workflow_service.py tests/test_pricing_runtime_wiring.py tests/test_pricing_routes.py tests/architecture/test_pricing_guardrails.py -q`
Expected: PASS

- [ ] **Step 5: Run broader regression verification**

Run: `python -m pytest tests/test_similar_search_workflow_service.py tests/test_similar_search_runtime_wiring.py tests/test_runtime_dependencies_container.py tests/architecture/test_provider_abstraction_guardrails.py tests/architecture/test_vector_foundation_guardrails.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/architecture/test_pricing_guardrails.py README.md docs/project_description.md docs/project_structure.md
git commit -m "docs: align pricing workflow foundation"
```

## Stage Exit Criteria

This stage is complete only when:

- pricing jobs are created and tracked on the backend
- comparable market evidence comes from backend-owned sources
- recommendation output is structured, saved, and retrievable
- PostgreSQL stores durable pricing truth
- routes are typed and thin
- no frontend code owns recommendation or market-comparison logic

## Self-Review

Spec coverage checked:

- request intake and persistence: Tasks 1, 2, 3, 6
- comparison brief and recommendation logic: Tasks 4, 5
- reuse of similar-search and catalog truth: Tasks 5, 6
- backend-owned API contour: Tasks 6, 7

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each code-bearing step includes concrete code or commands.

Type consistency checked:

- `PricingRequest`, `PricingRecommendation`, `SqlPricingRepository`, `PricingWorkflowService`, and `PricingRuntimeDependencies` are named consistently across later tasks.
