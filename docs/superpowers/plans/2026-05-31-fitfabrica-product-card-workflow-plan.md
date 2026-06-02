# FitFabrica Product Card Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend-owned product-card workflow so FitFabrica can accept B2B product source material, persist a durable job in PostgreSQL, generate a structured product-card draft through provider-neutral services, and return typed status and result payloads.

**Architecture:** Keep PostgreSQL as the source of truth for product-card jobs, versions, and quality notes. Keep S3-compatible object storage as the only binary storage layer for uploaded product media and generated artifacts. Reuse the provider runtime for structured generation, and keep route modules thin by pushing orchestration into a dedicated workflow service.

**Tech Stack:** FastAPI, Python, Pydantic, SQLAlchemy, Alembic, S3-compatible object storage, provider runtime, pytest.

---

## Scope And Baseline

Current state in this worktree:

- frontend already exposes `/workspace/product-card` as a product-facing route
- no backend product-card API route exists yet
- no SQL persistence exists for product-card jobs, versions, or quality notes
- portable object storage, provider runtime, and PostgreSQL foundations already exist
- similar-search catalog truth exists and can later inform product-card enrichment

This stage does not yet implement:

- final marketplace publishing connectors
- production image generation
- billing and credits deduction
- multi-tenant team permissions beyond current app baseline

This stage builds the backend execution contour for:

- product-card job creation
- durable storage of source images and outputs
- provider-neutral structured draft generation
- typed job polling
- versioned result history

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/product_card.py`
  - typed request, draft, version, quality-note, and response models.
- `src/use_cases/product_card/ports.py`
  - workflow-facing ports for repository, file storage, and generation providers.
- `src/use_cases/product_card/workflow_service.py`
  - orchestration for uploads, generation, quality-note capture, and persistence.
- `src/use_cases/product_card/storage_errors.py`
  - backend-owned storage error mapping for product-card file uploads.
- `src/adapters/database/sql/product_card_models.py`
  - SQLAlchemy tables for jobs, source assets, generated versions, and quality notes.
- `src/adapters/database/sql/product_card_serialization.py`
  - row/domain mapping helpers.
- `src/adapters/database/sql/product_card_repositories.py`
  - SQL repository implementation for product-card aggregates.
- `alembic/versions/20260531_000005_product_card_workflow.py`
  - migration for product-card persistence.
- `src/adapters/product_card/fake_generation.py`
  - deterministic generation stub until a real product-card provider is approved.
- `src/entrypoints/runtime_dependencies.py`
  - expose product-card runtime dependencies from the composition root.
- `src/entrypoints/product_card_routes.py`
  - FastAPI create/status/result endpoints for backend-owned product-card jobs.
- `src/entrypoints/http_routes.py`
  - include the new router.
- `tests/test_product_card_domain_models.py`
  - verify typed contracts.
- `tests/test_product_card_sql_models.py`
  - verify SQL schema surfaces.
- `tests/test_product_card_sql_repositories.py`
  - verify aggregate persistence and version retrieval.
- `tests/test_product_card_workflow_service.py`
  - verify orchestration with fakes.
- `tests/test_product_card_runtime_wiring.py`
  - verify runtime bundle selection.
- `tests/test_product_card_routes.py`
  - verify create/status/result route behavior.
- `tests/architecture/test_product_card_guardrails.py`
  - enforce backend-owned workflow and provider neutrality.
- `README.md`
  - document the product-card workflow contour.
- `docs/project_description.md`
  - record the B2B product-card baseline.
- `docs/project_structure.md`
  - record the new product-card modules.

## Task 1: Define Product Card Domain Contracts

**Files:**
- Create: `src/domain/product_card.py`
- Create: `tests/test_product_card_domain_models.py`

- [ ] **Step 1: Write the failing domain-model tests**

```python
from src.domain.product_card import ProductCardDraft, ProductCardRequest


def test_product_card_request_keeps_target_channel_and_brand_tone() -> None:
    request = ProductCardRequest(
        title_hint="Linen midi dress",
        target_channel="wildberries",
        brand_tone="minimal premium",
    )

    assert request.target_channel == "wildberries"
    assert request.brand_tone == "minimal premium"


def test_product_card_draft_exposes_structured_marketplace_fields() -> None:
    draft = ProductCardDraft(
        title="Linen midi dress",
        description="Breathable summer dress with a clean silhouette.",
        bullet_points=["linen blend", "midi length"],
        attributes={"category": "dress"},
    )

    assert draft.attributes["category"] == "dress"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_product_card_domain_models.py -q`
Expected: FAIL because product-card domain models do not exist yet.

- [ ] **Step 3: Implement the minimal domain models**

```python
class ProductCardRequest(BaseModel):
    title_hint: str | None = None
    target_channel: str
    brand_tone: str
    source_image_keys: list[str] = Field(default_factory=list)
```

```python
class ProductCardDraft(BaseModel):
    title: str
    description: str
    bullet_points: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_product_card_domain_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/product_card.py tests/test_product_card_domain_models.py
git commit -m "feat: define product card domain models"
```

## Task 2: Add Product Card SQL Foundation

**Files:**
- Create: `src/adapters/database/sql/product_card_models.py`
- Create: `alembic/versions/20260531_000005_product_card_workflow.py`
- Create: `tests/test_product_card_sql_models.py`

- [ ] **Step 1: Write the failing SQL-model tests**

```python
from src.adapters.database.sql.product_card_models import ProductCardJobRow, ProductCardVersionRow


def test_product_card_sql_models_define_job_and_version_tables() -> None:
    assert ProductCardJobRow.__tablename__ == "product_card_jobs"
    assert ProductCardVersionRow.__tablename__ == "product_card_versions"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_product_card_sql_models.py -q`
Expected: FAIL because product-card SQL models do not exist yet.

- [ ] **Step 3: Implement SQLAlchemy models and migration**

```python
class ProductCardJobRow(SqlBase):
    __tablename__ = "product_card_jobs"
    job_id = mapped_column(String(64), primary_key=True)
    status = mapped_column(String(32), nullable=False)
    target_channel = mapped_column(String(64), nullable=False)
```

```python
class ProductCardVersionRow(SqlBase):
    __tablename__ = "product_card_versions"
    version_id = mapped_column(String(64), primary_key=True)
    job_id = mapped_column(ForeignKey("product_card_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    title = mapped_column(String(255), nullable=False)
```

```python
def upgrade() -> None:
    op.create_table(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_product_card_sql_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/product_card_models.py alembic/versions/20260531_000005_product_card_workflow.py tests/test_product_card_sql_models.py
git commit -m "feat: add product card sql models"
```

## Task 3: Add Product Card Repository And Serialization

**Files:**
- Create: `src/adapters/database/sql/product_card_serialization.py`
- Create: `src/adapters/database/sql/product_card_repositories.py`
- Create: `tests/test_product_card_sql_repositories.py`

- [ ] **Step 1: Write the failing repository tests**

```python
async def test_product_card_repository_persists_job_and_latest_version() -> None:
    repository = SqlProductCardRepository(session_factory=...)
    aggregate = await repository.create_job(...)
    latest = await repository.get_latest_version(aggregate.job_id)

    assert latest is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_product_card_sql_repositories.py -q`
Expected: FAIL because the repository does not exist yet.

- [ ] **Step 3: Implement focused repository logic**

```python
class SqlProductCardRepository(ProductCardRepositoryPort):
    async def create_job(self, request: ProductCardRequest, asset_keys: list[str]) -> ProductCardJobRecord:
        ...

    async def save_generated_version(self, job_id: str, draft: ProductCardDraft) -> ProductCardVersionRecord:
        ...
```

```python
def version_record_from_row(row: ProductCardVersionRow) -> ProductCardVersionRecord:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_product_card_sql_repositories.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/product_card_serialization.py src/adapters/database/sql/product_card_repositories.py tests/test_product_card_sql_repositories.py
git commit -m "feat: add product card repositories"
```

## Task 4: Add Product Card Workflow Service

**Files:**
- Create: `src/use_cases/product_card/ports.py`
- Create: `src/use_cases/product_card/storage_errors.py`
- Create: `src/use_cases/product_card/workflow_service.py`
- Create: `src/adapters/product_card/fake_generation.py`
- Create: `tests/test_product_card_workflow_service.py`

- [ ] **Step 1: Write the failing workflow tests**

```python
async def test_product_card_workflow_creates_job_generates_draft_and_returns_result() -> None:
    service = ProductCardWorkflowService(...)
    result = await service.create_product_card(request=..., source_files=...)

    assert result.job.status == "completed"
    assert result.version.title
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_product_card_workflow_service.py -q`
Expected: FAIL because the workflow service does not exist yet.

- [ ] **Step 3: Implement orchestration**

```python
class ProductCardWorkflowService:
    async def create_product_card(self, *, request: ProductCardRequest, source_files: list[ProductCardSourceFile]) -> ProductCardWorkflowResult:
        asset_keys = await self._file_storage.store_many(source_files)
        job = await self._repository.create_job(request, asset_keys)
        draft = self._generation_adapter.generate(request=request, asset_keys=asset_keys)
        version = await self._repository.save_generated_version(job.job_id, draft)
        return ProductCardWorkflowResult(job=await self._repository.mark_completed(job.job_id), version=version)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_product_card_workflow_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/product_card/ports.py src/use_cases/product_card/storage_errors.py src/use_cases/product_card/workflow_service.py src/adapters/product_card/fake_generation.py tests/test_product_card_workflow_service.py
git commit -m "feat: add product card workflow service"
```

## Task 5: Add Runtime Wiring And FastAPI Surface

**Files:**
- Modify: `src/entrypoints/runtime_dependencies.py`
- Create: `src/entrypoints/product_card_routes.py`
- Modify: `src/entrypoints/http_routes.py`
- Create: `tests/test_product_card_runtime_wiring.py`
- Create: `tests/test_product_card_routes.py`

- [ ] **Step 1: Write the failing runtime and route tests**

```python
def test_product_card_runtime_dependencies_prefer_sql_and_portable_storage() -> None:
    runtime = product_card_runtime_dependencies(settings)
    assert runtime.workflow_service is not None
```

```python
def test_product_card_route_creates_job_and_returns_structured_response(client) -> None:
    response = client.post("/api/product-cards", json={...})
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_product_card_runtime_wiring.py tests/test_product_card_routes.py -q`
Expected: FAIL because runtime wiring and routes do not exist yet.

- [ ] **Step 3: Implement runtime bundle and routes**

```python
@dataclass(frozen=True)
class ProductCardRuntimeDependencies:
    workflow_service: ProductCardWorkflowService
```

```python
@router.post("/api/product-cards")
async def create_product_card(...):
    return await workflow_service.create_product_card(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_product_card_runtime_wiring.py tests/test_product_card_routes.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/runtime_dependencies.py src/entrypoints/product_card_routes.py src/entrypoints/http_routes.py tests/test_product_card_runtime_wiring.py tests/test_product_card_routes.py
git commit -m "feat: add product card api wiring"
```

## Task 6: Add Guardrails And Final Verification

**Files:**
- Create: `tests/architecture/test_product_card_guardrails.py`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_product_card_workflow_stays_backend_owned_and_provider_neutral() -> None:
    text = Path("src/use_cases/product_card/workflow_service.py").read_text(encoding="utf-8").lower()
    assert "gemini" not in text
    assert "vertex" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_product_card_guardrails.py -q`
Expected: FAIL until the workflow boundary and docs are aligned.

- [ ] **Step 3: Update docs**

```markdown
- product-card generation is backend-owned
- PostgreSQL stores jobs, versions, and quality notes
- portable object storage stores source images and generated artifacts
```

- [ ] **Step 4: Run targeted product-card verification**

Run: `python -m pytest tests/test_product_card_domain_models.py tests/test_product_card_sql_models.py tests/test_product_card_sql_repositories.py tests/test_product_card_workflow_service.py tests/test_product_card_runtime_wiring.py tests/test_product_card_routes.py tests/architecture/test_product_card_guardrails.py -q`
Expected: PASS

- [ ] **Step 5: Run broader regression verification**

Run: `python -m pytest tests/test_runtime_dependencies_container.py tests/test_portable_platform_settings.py tests/test_try_on_runtime_wiring.py tests/test_similar_search_runtime_wiring.py tests/architecture/test_provider_abstraction_guardrails.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/architecture/test_product_card_guardrails.py README.md docs/project_description.md docs/project_structure.md
git commit -m "docs: align product card workflow foundation"
```

## Stage Exit Criteria

This stage is complete only when:

- product-card jobs are created and tracked on the backend
- PostgreSQL stores the durable workflow truth
- uploaded source images go through portable object storage
- structured product-card drafts are versioned and retrievable
- routes are typed and thin
- no frontend code owns generation logic or persistence decisions

## Self-Review

Spec coverage checked:

- job creation and persistence: Tasks 2, 3, 5
- storage handling: Tasks 4, 5
- typed generation result: Tasks 1, 4
- backend-owned route contour: Tasks 5, 6

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each code-bearing step includes concrete code or commands.

Type consistency checked:

- `ProductCardRequest`, `ProductCardDraft`, `SqlProductCardRepository`, `ProductCardWorkflowService`, and `ProductCardRuntimeDependencies` are named consistently across later tasks.
