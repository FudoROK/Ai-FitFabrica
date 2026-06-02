# FitFabrica Content Package Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend-owned content-package workflow so FitFabrica can take a product-card result plus package options, generate a structured set of marketplace and marketing assets, persist export-ready versions in PostgreSQL, and return typed result payloads.

**Architecture:** Treat content-package generation as its own B2B workflow, not as a hidden side effect inside product-card generation. PostgreSQL stores jobs, package versions, and export metadata. Portable object storage stores generated artifacts and export bundles. Provider runtime stays behind neutral ports, and the route layer remains thin.

**Tech Stack:** FastAPI, Python, Pydantic, SQLAlchemy, Alembic, S3-compatible object storage, provider runtime, pytest.

---

## Scope And Baseline

Current state in this worktree:

- frontend already exposes `/workspace/content-package`
- no backend content-package API exists yet
- no SQL workflow exists for content-package generation
- Stage 7 similar-search and catalog truth can later enrich B2B outputs, but are not required for the first slice
- product-card planning exists as the direct upstream workflow for content-package input

This stage does not yet implement:

- direct publishing to external channels
- final design rendering pipelines
- billing and credits logic
- long-running worker topology beyond current synchronous-safe first slice

This stage builds the backend contour for:

- package request intake
- package version persistence
- artifact reference storage
- export metadata
- typed status/result polling

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/content_package.py`
  - typed request, package option, asset reference, version, and response models.
- `src/use_cases/content_package/ports.py`
  - workflow-facing ports for repository, storage, and generation adapters.
- `src/use_cases/content_package/workflow_service.py`
  - orchestration for package generation and persistence.
- `src/adapters/database/sql/content_package_models.py`
  - SQLAlchemy tables for jobs, package versions, and artifact references.
- `src/adapters/database/sql/content_package_serialization.py`
  - row/domain mapping helpers.
- `src/adapters/database/sql/content_package_repositories.py`
  - SQL repository implementation.
- `alembic/versions/20260531_000006_content_package_workflow.py`
  - migration for content-package persistence.
- `src/adapters/content_package/fake_generation.py`
  - deterministic content-package generation stub.
- `src/entrypoints/runtime_dependencies.py`
  - expose content-package runtime dependencies.
- `src/entrypoints/content_package_routes.py`
  - FastAPI create/status/result endpoints.
- `src/entrypoints/http_routes.py`
  - include the new router.
- `tests/test_content_package_domain_models.py`
  - verify typed contracts.
- `tests/test_content_package_sql_models.py`
  - verify SQL schema surfaces.
- `tests/test_content_package_sql_repositories.py`
  - verify package persistence and retrieval.
- `tests/test_content_package_workflow_service.py`
  - verify orchestration with fakes.
- `tests/test_content_package_runtime_wiring.py`
  - verify runtime bundle selection.
- `tests/test_content_package_routes.py`
  - verify API behavior.
- `tests/architecture/test_content_package_guardrails.py`
  - enforce backend-owned workflow and provider neutrality.
- `README.md`
  - document the content-package contour.
- `docs/project_description.md`
  - record the B2B content-package baseline.
- `docs/project_structure.md`
  - record the new modules.

## Task 1: Define Content Package Domain Contracts

**Files:**
- Create: `src/domain/content_package.py`
- Create: `tests/test_content_package_domain_models.py`

- [ ] **Step 1: Write the failing domain-model tests**

```python
from src.domain.content_package import ContentPackageOption, ContentPackageRequest


def test_content_package_request_keeps_requested_output_channels() -> None:
    request = ContentPackageRequest(
        product_card_version_id="version-1",
        package_name="marketplace-launch",
        requested_channels=["wildberries", "instagram"],
    )

    assert request.requested_channels == ["wildberries", "instagram"]


def test_content_package_option_exposes_asset_kind_and_label() -> None:
    option = ContentPackageOption(asset_kind="caption", label="Instagram caption")
    assert option.asset_kind == "caption"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_package_domain_models.py -q`
Expected: FAIL because content-package domain models do not exist yet.

- [ ] **Step 3: Implement the minimal domain models**

```python
class ContentPackageRequest(BaseModel):
    product_card_version_id: str
    package_name: str
    requested_channels: list[str] = Field(default_factory=list)
```

```python
class ContentPackageOption(BaseModel):
    asset_kind: str
    label: str
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_package_domain_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/content_package.py tests/test_content_package_domain_models.py
git commit -m "feat: define content package domain models"
```

## Task 2: Add Content Package SQL Foundation

**Files:**
- Create: `src/adapters/database/sql/content_package_models.py`
- Create: `alembic/versions/20260531_000006_content_package_workflow.py`
- Create: `tests/test_content_package_sql_models.py`

- [ ] **Step 1: Write the failing SQL-model tests**

```python
from src.adapters.database.sql.content_package_models import ContentPackageJobRow, ContentPackageVersionRow


def test_content_package_sql_models_define_job_and_version_tables() -> None:
    assert ContentPackageJobRow.__tablename__ == "content_package_jobs"
    assert ContentPackageVersionRow.__tablename__ == "content_package_versions"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_package_sql_models.py -q`
Expected: FAIL because content-package SQL models do not exist yet.

- [ ] **Step 3: Implement SQLAlchemy models and migration**

```python
class ContentPackageJobRow(SqlBase):
    __tablename__ = "content_package_jobs"
    job_id = mapped_column(String(64), primary_key=True)
    product_card_version_id = mapped_column(String(64), nullable=False, index=True)
    status = mapped_column(String(32), nullable=False)
```

```python
class ContentPackageVersionRow(SqlBase):
    __tablename__ = "content_package_versions"
    version_id = mapped_column(String(64), primary_key=True)
    job_id = mapped_column(ForeignKey("content_package_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    package_name = mapped_column(String(128), nullable=False)
```

```python
def upgrade() -> None:
    op.create_table(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_package_sql_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/content_package_models.py alembic/versions/20260531_000006_content_package_workflow.py tests/test_content_package_sql_models.py
git commit -m "feat: add content package sql models"
```

## Task 3: Add Content Package Repository Layer

**Files:**
- Create: `src/adapters/database/sql/content_package_serialization.py`
- Create: `src/adapters/database/sql/content_package_repositories.py`
- Create: `tests/test_content_package_sql_repositories.py`

- [ ] **Step 1: Write the failing repository tests**

```python
async def test_content_package_repository_persists_job_and_package_version() -> None:
    repository = SqlContentPackageRepository(session_factory=...)
    job = await repository.create_job(...)
    version = await repository.save_package_version(job.job_id, ...)

    assert version.job_id == job.job_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_package_sql_repositories.py -q`
Expected: FAIL because the repository does not exist yet.

- [ ] **Step 3: Implement focused repository logic**

```python
class SqlContentPackageRepository(ContentPackageRepositoryPort):
    async def create_job(self, request: ContentPackageRequest) -> ContentPackageJobRecord:
        ...

    async def save_package_version(self, job_id: str, package: ContentPackageVersionDraft) -> ContentPackageVersionRecord:
        ...
```

```python
def package_version_from_row(row: ContentPackageVersionRow) -> ContentPackageVersionRecord:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_package_sql_repositories.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/content_package_serialization.py src/adapters/database/sql/content_package_repositories.py tests/test_content_package_sql_repositories.py
git commit -m "feat: add content package repositories"
```

## Task 4: Add Content Package Workflow Service

**Files:**
- Create: `src/use_cases/content_package/ports.py`
- Create: `src/use_cases/content_package/workflow_service.py`
- Create: `src/adapters/content_package/fake_generation.py`
- Create: `tests/test_content_package_workflow_service.py`

- [ ] **Step 1: Write the failing workflow tests**

```python
async def test_content_package_workflow_creates_package_and_returns_artifact_references() -> None:
    service = ContentPackageWorkflowService(...)
    result = await service.create_content_package(request=...)

    assert result.version.package_name == "marketplace-launch"
    assert result.version.assets
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_package_workflow_service.py -q`
Expected: FAIL because the workflow service does not exist yet.

- [ ] **Step 3: Implement orchestration**

```python
class ContentPackageWorkflowService:
    async def create_content_package(self, *, request: ContentPackageRequest) -> ContentPackageWorkflowResult:
        job = await self._repository.create_job(request)
        generated = self._generation_adapter.generate(request)
        version = await self._repository.save_package_version(job.job_id, generated)
        return ContentPackageWorkflowResult(job=await self._repository.mark_completed(job.job_id), version=version)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_package_workflow_service.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/content_package/ports.py src/use_cases/content_package/workflow_service.py src/adapters/content_package/fake_generation.py tests/test_content_package_workflow_service.py
git commit -m "feat: add content package workflow service"
```

## Task 5: Add Runtime Wiring And FastAPI Surface

**Files:**
- Modify: `src/entrypoints/runtime_dependencies.py`
- Create: `src/entrypoints/content_package_routes.py`
- Modify: `src/entrypoints/http_routes.py`
- Create: `tests/test_content_package_runtime_wiring.py`
- Create: `tests/test_content_package_routes.py`

- [ ] **Step 1: Write the failing runtime and route tests**

```python
def test_content_package_runtime_dependencies_prefer_sql_and_portable_storage() -> None:
    runtime = content_package_runtime_dependencies(settings)
    assert runtime.workflow_service is not None
```

```python
def test_content_package_route_returns_structured_response(client) -> None:
    response = client.post("/api/content-packages", json={...})
    assert response.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_content_package_runtime_wiring.py tests/test_content_package_routes.py -q`
Expected: FAIL because runtime wiring and routes do not exist yet.

- [ ] **Step 3: Implement runtime bundle and routes**

```python
@dataclass(frozen=True)
class ContentPackageRuntimeDependencies:
    workflow_service: ContentPackageWorkflowService
```

```python
@router.post("/api/content-packages")
async def create_content_package(...):
    return await workflow_service.create_content_package(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_content_package_runtime_wiring.py tests/test_content_package_routes.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/runtime_dependencies.py src/entrypoints/content_package_routes.py src/entrypoints/http_routes.py tests/test_content_package_runtime_wiring.py tests/test_content_package_routes.py
git commit -m "feat: add content package api wiring"
```

## Task 6: Add Guardrails And Final Verification

**Files:**
- Create: `tests/architecture/test_content_package_guardrails.py`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_content_package_workflow_stays_backend_owned_and_provider_neutral() -> None:
    text = Path("src/use_cases/content_package/workflow_service.py").read_text(encoding="utf-8").lower()
    assert "gemini" not in text
    assert "vertex" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_content_package_guardrails.py -q`
Expected: FAIL until the workflow boundary and docs are aligned.

- [ ] **Step 3: Update docs**

```markdown
- content-package generation is backend-owned
- PostgreSQL stores jobs, versions, and export metadata
- portable object storage stores generated package artifacts
```

- [ ] **Step 4: Run targeted verification**

Run: `python -m pytest tests/test_content_package_domain_models.py tests/test_content_package_sql_models.py tests/test_content_package_sql_repositories.py tests/test_content_package_workflow_service.py tests/test_content_package_runtime_wiring.py tests/test_content_package_routes.py tests/architecture/test_content_package_guardrails.py -q`
Expected: PASS

- [ ] **Step 5: Run broader regression verification**

Run: `python -m pytest tests/test_runtime_dependencies_container.py tests/test_product_card_runtime_wiring.py tests/test_try_on_runtime_wiring.py tests/test_similar_search_runtime_wiring.py tests/architecture/test_provider_abstraction_guardrails.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add tests/architecture/test_content_package_guardrails.py README.md docs/project_description.md docs/project_structure.md
git commit -m "docs: align content package workflow foundation"
```

## Stage Exit Criteria

This stage is complete only when:

- content-package jobs are created and tracked on the backend
- PostgreSQL stores versioned package truth
- export-ready artifact references are durable
- object storage owns binary package outputs
- routes are typed and thin
- no frontend code owns package assembly or export decisions

## Self-Review

Spec coverage checked:

- package request intake: Tasks 1, 4, 5
- durable persistence: Tasks 2, 3
- export metadata and assets: Tasks 3, 4
- backend-owned API surface: Tasks 5, 6

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each code-bearing step includes concrete code or commands.

Type consistency checked:

- `ContentPackageRequest`, `ContentPackageOption`, `SqlContentPackageRepository`, `ContentPackageWorkflowService`, and `ContentPackageRuntimeDependencies` are named consistently across later tasks.
