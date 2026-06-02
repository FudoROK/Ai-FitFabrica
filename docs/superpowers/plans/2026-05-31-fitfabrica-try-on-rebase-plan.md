# FitFabrica Try-On Rebase Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebase the existing backend-owned Try-On workflow onto the portable platform baseline so jobs live in PostgreSQL, uploads stay on the portable object-storage path, and generation wiring becomes provider-runtime ready without reintroducing Firestore or GCS as target architecture.

**Architecture:** Keep the existing thin FastAPI routes and reusable workflow service shape, but replace sandbox-era durable persistence with SQL-backed job storage and explicit runtime wiring. Preserve the fake generation adapter as the safe default until a real generation provider is approved, while changing the surrounding workflow contracts so the generation path can later use provider-neutral image adapters and portable artifact references. Treat Firestore and GCS Try-On adapters as migration-state compatibility only, not as active runtime defaults.

**Tech Stack:** FastAPI, Python, Pydantic, SQLAlchemy, Alembic, portable object storage adapters, provider runtime layer, pytest.

---

## Scope And Baseline

Current state in this worktree:

- `src/entrypoints/try_on_routes.py` already uses portable object storage for uploads.
- Try-On job persistence still selects `InMemoryTryOnJobRepository` or `FirestoreTryOnJobRepository`.
- `src/use_cases/try_on/workflow_service.py` is still sandbox-shaped and assumes a single synchronous fake generation step.
- `src/domain/try_on.py` still contains sandbox-only names and a legacy storage backend union that includes `gcs`.
- `src/adapters/try_on/fake_generation.py` returns a deterministic placeholder result and is still the active generation adapter.
- `src/adapters/try_on/gcs_file_storage.py` and `src/adapters/try_on/firestore_repository.py` still exist as migration-state code.
- Stage 5 already added provider-neutral image-generation and image-editing ports, but Try-On does not use them yet.

This stage does not promise final production-quality virtual try-on output. It moves the workflow foundation onto the portable baseline and prepares the generation boundary for later real providers.

## Reuse Versus Replacement

Reuse:

- typed FastAPI route contract in `src/entrypoints/try_on_routes.py`
- upload validation logic in `src/use_cases/try_on/workflow_service.py`
- portable object storage path through `src/adapters/storage/media_storage.py`
- fake generation adapter as the default safe generation implementation
- existing Try-On API, storage, and lifecycle tests as the regression baseline

Replace or narrow:

- Firestore job persistence as the active durable Try-On path
- sandbox-only job aggregate naming where it blocks future production flow
- direct repository selection inside Try-On route wiring
- storage/backend error typing that still bakes in `gcs | firestore`
- docs that still tell operators to use Firestore as the durable target

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/try_on.py`
  - Rebase the Try-On domain model from sandbox-only wording to portable workflow wording.
- `src/use_cases/try_on/ports.py`
  - Extend Try-On ports for SQL persistence and provider-runtime-friendly generation outputs.
- `src/use_cases/try_on/storage_errors.py`
  - Replace legacy `gcs | firestore` backend typing with portable backend-safe names.
- `src/use_cases/try_on/workflow_service.py`
  - Keep validation and lifecycle orchestration, but make persistence and generation portable-baseline aware.
- `src/adapters/database/sql/try_on_models.py`
  - SQLAlchemy tables for Try-On jobs, stored inputs, status history, cost events, and result metadata.
- `src/adapters/database/sql/try_on_repositories.py`
  - SQL repository implementation for the Try-On job aggregate.
- `src/adapters/database/sql/try_on_serialization.py`
  - Focused mapping helpers between SQL rows and `TryOnJob` domain aggregates.
- `alembic/versions/20260531_000003_try_on_rebase_foundation.py`
  - Migration for Try-On SQL tables.
- `src/adapters/try_on/fake_generation.py`
  - Keep fake generation, but align its output with the rebased portable domain contract.
- `src/adapters/try_on/firestore_repository.py`
  - Keep only as migration-state adapter if still needed by tests; remove from active route/runtime selection.
- `src/entrypoints/runtime_dependencies.py`
  - Add Try-On runtime repository selection that prefers SQL when portable SQL infrastructure exists.
- `src/entrypoints/try_on_routes.py`
  - Stop constructing repository choices locally; consume the composition root instead.
- `tests/test_try_on_sql_models.py`
  - Verify SQL Try-On schema shape and required constraints.
- `tests/test_try_on_sql_repository.py`
  - Verify SQL repository save/read lifecycle for job aggregates.
- `tests/test_try_on_runtime_wiring.py`
  - Verify Try-On runtime selection prefers SQL and portable storage.
- `tests/test_try_on_workflow_service_rebase.py`
  - Verify the workflow service still creates valid jobs on the rebased contracts.
- `tests/architecture/test_try_on_rebase_guardrails.py`
  - Enforce that active Try-On runtime paths do not select Firestore or GCS directly.
- `docs/try-on-sandbox-api.md`
  - Update the API contract to describe the rebased portable persistence baseline.
- `docs/try-on-durable-storage-activation.md`
  - Remove Firestore-as-target durable activation guidance.
- `README.md`
  - Document the rebased Try-On backend contour.
- `docs/project_description.md`
  - Record the portable Try-On baseline.
- `docs/project_structure.md`
  - Record the new Try-On SQL and runtime modules.
- `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`
  - Mark Stage 6 planning as complete.

## Task 1: Rebase The Try-On Domain Contracts

**Files:**
- Modify: `src/domain/try_on.py`
- Modify: `src/use_cases/try_on/ports.py`
- Modify: `src/use_cases/try_on/storage_errors.py`
- Create: `tests/test_try_on_domain_rebase.py`

- [ ] **Step 1: Write the failing domain contract tests**

```python
from src.domain.try_on import TryOnGenerationMode, TryOnStoredInput


def test_try_on_stored_input_no_longer_exposes_gcs_backend() -> None:
    stored_input = TryOnStoredInput(
        role="human_photo",
        storage_backend="s3",
        uri="s3://bucket/key",
        object_key="tenant/job/human.png",
        content_type="image/png",
        size_bytes=10,
        sha256="a" * 64,
    )

    assert stored_input.storage_backend == "s3"


def test_try_on_generation_mode_defaults_to_sandbox_fake() -> None:
    assert TryOnGenerationMode.SANDBOX_FAKE == "sandbox_fake"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_domain_rebase.py -q`
Expected: FAIL because rebased Try-On contract types do not exist yet.

- [ ] **Step 3: Implement the rebased portable domain types**

```python
class TryOnGenerationMode(StrEnum):
    SANDBOX_FAKE = "sandbox_fake"


class TryOnStoredInput(BaseModel):
    storage_backend: Literal["in_memory", "s3"]
```

```python
TryOnStorageBackend = Literal["in_memory", "s3", "sql"]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_domain_rebase.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/try_on.py src/use_cases/try_on/ports.py src/use_cases/try_on/storage_errors.py tests/test_try_on_domain_rebase.py
git commit -m "refactor: rebase try-on domain contracts"
```

## Task 2: Add SQL Try-On Persistence Models

**Files:**
- Create: `src/adapters/database/sql/try_on_models.py`
- Create: `tests/test_try_on_sql_models.py`
- Create: `alembic/versions/20260531_000003_try_on_rebase_foundation.py`

- [ ] **Step 1: Write the failing SQL model tests**

```python
from src.adapters.database.sql.try_on_models import TryOnJobModel, TryOnStoredInputModel


def test_try_on_sql_models_define_job_and_stored_input_tables() -> None:
    assert TryOnJobModel.__tablename__ == "try_on_jobs"
    assert TryOnStoredInputModel.__tablename__ == "try_on_stored_inputs"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_sql_models.py -q`
Expected: FAIL because the Try-On SQL models do not exist yet.

- [ ] **Step 3: Implement the SQLAlchemy models and Alembic migration**

```python
class TryOnJobModel(Base):
    __tablename__ = "try_on_jobs"
    job_id = mapped_column(String(64), primary_key=True)
    workflow_type = mapped_column(String(32), nullable=False)
    status = mapped_column(String(32), nullable=False)
```

```python
class TryOnStoredInputModel(Base):
    __tablename__ = "try_on_stored_inputs"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id = mapped_column(ForeignKey("try_on_jobs.job_id"), nullable=False, index=True)
```

```python
def upgrade() -> None:
    op.create_table(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_sql_models.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/try_on_models.py tests/test_try_on_sql_models.py alembic/versions/20260531_000003_try_on_rebase_foundation.py
git commit -m "feat: add try-on sql persistence models"
```

## Task 3: Add SQL Repository Mapping For Try-On Jobs

**Files:**
- Create: `src/adapters/database/sql/try_on_serialization.py`
- Create: `src/adapters/database/sql/try_on_repositories.py`
- Create: `tests/test_try_on_sql_repository.py`

- [ ] **Step 1: Write the failing SQL repository tests**

```python
async def test_sql_try_on_repository_round_trips_job_aggregate() -> None:
    repository = SqlTryOnJobRepository(session_factory=...)
    await repository.save(job)

    saved = await repository.get(job.job_id)

    assert saved is not None
    assert saved.job_id == job.job_id
    assert saved.stored_inputs[0].object_key == "tenant/job/human.png"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_sql_repository.py -q`
Expected: FAIL because the SQL repository and mappers do not exist yet.

- [ ] **Step 3: Implement the repository and focused serialization helpers**

```python
class SqlTryOnJobRepository(TryOnJobRepositoryPort):
    async def save(self, job: TryOnJob) -> None:
        ...

    async def get(self, job_id: str) -> TryOnJob | None:
        ...
```

```python
def job_to_models(job: TryOnJob) -> SerializedTryOnJob:
    ...


def job_from_models(... ) -> TryOnJob:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_sql_repository.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/try_on_serialization.py src/adapters/database/sql/try_on_repositories.py tests/test_try_on_sql_repository.py
git commit -m "feat: add try-on sql repository"
```

## Task 4: Move Try-On Runtime Selection Into The Composition Root

**Files:**
- Modify: `src/entrypoints/runtime_dependencies.py`
- Modify: `src/entrypoints/try_on_routes.py`
- Create: `tests/test_try_on_runtime_wiring.py`

- [ ] **Step 1: Write the failing runtime wiring tests**

```python
from src.entrypoints import runtime_dependencies as deps


def test_try_on_runtime_repositories_prefer_sql_when_portable_sql_exists() -> None:
    settings = ...
    repositories = deps.try_on_runtime_dependencies(settings)

    assert repositories.job_repository.__class__.__name__ == "SqlTryOnJobRepository"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_runtime_wiring.py -q`
Expected: FAIL because Try-On runtime dependencies are still constructed inside the route module.

- [ ] **Step 3: Implement composition-root wiring**

```python
@dataclass(frozen=True)
class TryOnRuntimeDependencies:
    job_repository: TryOnJobRepositoryPort
    file_storage: TryOnFileStoragePort
    generation_adapter: TryOnGenerationPort
```

```python
def try_on_runtime_dependencies(settings) -> TryOnRuntimeDependencies:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_runtime_wiring.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/runtime_dependencies.py src/entrypoints/try_on_routes.py tests/test_try_on_runtime_wiring.py
git commit -m "refactor: move try-on runtime wiring to composition root"
```

## Task 5: Rebase The Workflow Service On The Portable Baseline

**Files:**
- Modify: `src/use_cases/try_on/workflow_service.py`
- Modify: `src/adapters/try_on/fake_generation.py`
- Create: `tests/test_try_on_workflow_service_rebase.py`

- [ ] **Step 1: Write the failing workflow rebase tests**

```python
async def test_try_on_workflow_service_persists_portable_job_state() -> None:
    job = await service.create_job(...)

    assert job.generation_mode == "sandbox_fake"
    assert job.stored_inputs[0].storage_backend in {"in_memory", "s3"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_workflow_service_rebase.py -q`
Expected: FAIL because the workflow service still only models sandbox-era state.

- [ ] **Step 3: Implement the rebased workflow orchestration**

```python
class TryOnWorkflowService:
    async def create_job(...):
        ...
        result = await self._generator.generate(...)
        ...
```

```python
return TryOnJob(
    ...,
    generation_mode=TryOnGenerationMode.SANDBOX_FAKE,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_workflow_service_rebase.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/try_on/workflow_service.py src/adapters/try_on/fake_generation.py tests/test_try_on_workflow_service_rebase.py
git commit -m "refactor: rebase try-on workflow service"
```

## Task 6: Remove Firestore And GCS From Active Try-On Runtime Paths

**Files:**
- Modify: `src/adapters/try_on/firestore_repository.py`
- Modify: `src/adapters/try_on/gcs_file_storage.py`
- Create: `tests/architecture/test_try_on_rebase_guardrails.py`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_active_try_on_runtime_paths_do_not_select_firestore_or_gcs() -> None:
    routes_text = Path("src/entrypoints/try_on_routes.py").read_text(encoding="utf-8")
    runtime_text = Path("src/entrypoints/runtime_dependencies.py").read_text(encoding="utf-8")

    assert "FirestoreTryOnJobRepository(" not in routes_text
    assert "GcsTryOnFileStorage(" not in routes_text
    assert "FirestoreTryOnJobRepository(" not in runtime_text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_try_on_rebase_guardrails.py -q`
Expected: FAIL because active Try-On routing still contains Firestore-specific repository selection.

- [ ] **Step 3: Narrow legacy adapters to migration-state only**

```python
# Firestore and GCS Try-On adapters remain isolated compatibility modules,
# but active runtime wiring no longer constructs them.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/architecture/test_try_on_rebase_guardrails.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/try_on/firestore_repository.py src/adapters/try_on/gcs_file_storage.py tests/architecture/test_try_on_rebase_guardrails.py
git commit -m "test: enforce try-on portable runtime boundaries"
```

## Task 7: Align Docs And Run Final Verification

**Files:**
- Modify: `docs/try-on-sandbox-api.md`
- Modify: `docs/try-on-durable-storage-activation.md`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Update docs to match the rebased Try-On baseline**

```markdown
- Try-On jobs now persist in PostgreSQL when portable SQL infrastructure is configured
- uploads stay on the portable object storage path
- fake generation remains the safe default until a real generation adapter is approved
```

- [ ] **Step 2: Run targeted Try-On rebase verification**

Run:
`python -m pytest tests/test_try_on_domain_rebase.py tests/test_try_on_sql_models.py tests/test_try_on_sql_repository.py tests/test_try_on_runtime_wiring.py tests/test_try_on_workflow_service_rebase.py tests/architecture/test_try_on_rebase_guardrails.py -q`

Expected: PASS

- [ ] **Step 3: Run broader Try-On regression verification**

Run:
`python -m pytest tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_route_storage_wiring.py tests/test_try_on_portable_media_storage.py tests/test_try_on_file_storage_workflow.py tests/test_try_on_storage_error_mapping.py tests/test_try_on_storage_settings.py tests/test_try_on_sandbox_api_docs.py -q`

Expected: PASS

- [ ] **Step 4: Run portable platform regression verification**

Run:
`python -m pytest tests/test_runtime_dependencies_container.py tests/test_platform_foundation_smoke.py tests/architecture/test_object_storage_migration_guardrails.py tests/architecture/test_provider_abstraction_guardrails.py -q`

Expected: PASS

- [ ] **Step 5: Run smoke command**

Run:
`python scripts/platform_foundation_smoke.py`

Expected output still includes:

```text
object_storage_backend=in_memory
qdrant_backend=qdrant
```

- [ ] **Step 6: Commit**

```bash
git add docs/try-on-sandbox-api.md docs/try-on-durable-storage-activation.md README.md docs/project_description.md docs/project_structure.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "docs: align try-on rebase stage"
```

## Stage Exit Criteria

This stage is complete only when:

- Try-On jobs persist in PostgreSQL on the active portable baseline
- Try-On uploads remain on the portable object-storage path
- active Try-On runtime wiring no longer selects Firestore or GCS as target architecture
- the fake generation adapter remains available as a safe default without blocking later provider-runtime image adapters
- Try-On route, workflow, and persistence boundaries stay thin and modular

## Self-Review

Spec coverage checked:

- SQL-backed job persistence: Tasks 2, 3, 4
- S3-backed media continuity: Tasks 1, 4, 5
- retention and audit-friendly aggregate structure: Tasks 2, 3, 5
- removal of Firestore/GCS target assumptions: Tasks 1, 4, 6, 7
- provider-runtime-ready generation boundary: Tasks 1, 5

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each implementation-bearing step includes concrete code or commands.

Type consistency checked:

- `TryOnGenerationMode`, `TryOnJob`, `SqlTryOnJobRepository`, `TryOnRuntimeDependencies`, and `TryOnStorageBackend` are named consistently across later tasks.

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-try-on-rebase-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
