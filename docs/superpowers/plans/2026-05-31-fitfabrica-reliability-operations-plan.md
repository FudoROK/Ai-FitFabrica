# FitFabrica Reliability And Operations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first production reliability contour so FitFabrica can execute heavy workflows outside request-response paths, keep durable processing state, surface health and observability signals, and operate safely under sustained load.

**Architecture:** Keep request handlers thin and move long-running execution into backend-owned queue and worker components. Use PostgreSQL for durable workflow state, Redis for short-lived coordination and idempotency, and explicit runtime services for dispatch, leases, retries, and health reporting. Existing Pub/Sub and task-trigger code stays migration-state unless directly reused behind portable queue contracts.

**Tech Stack:** FastAPI, Python, PostgreSQL, Redis, SQLAlchemy, background workers, portable object storage, Qdrant, pytest.

---

## Scope And Baseline

Current state in this worktree:

- Try-On, product card, content package, pricing, similar-search, and billing workflows now exist as backend-owned services.
- Portable infrastructure already exposes PostgreSQL, Redis, object storage, and Qdrant clients.
- Pub/Sub push handling, rate limiting, and processing lease logic already exist in older contours.
- Health endpoint exists, but it does not yet reflect worker topology or durable queue readiness.
- Heavy workflows are still effectively synchronous from the application point of view.

This stage builds:

- portable queue and worker contract
- durable workflow dispatch records
- worker execution lease and retry policy
- runtime health and readiness surfaces for heavy-workflow operation
- observability and alerting primitives for queues and workers
- ops documentation for backups, replicas, exports, and failure handling

This stage does not yet implement:

- external Kubernetes autoscaling
- vendor-specific managed queue lock-in
- full billing-triggered compensation workflows
- marketplace connector fleet orchestration

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/operations.py`
  - typed queue job, worker lease, retry policy, and health snapshot models.
- `src/use_cases/operations/ports.py`
  - workflow-facing ports for queue publishing, worker claims, and health reads.
- `src/use_cases/operations/dispatch_service.py`
  - backend-owned dispatch logic for enqueueing workflow jobs with idempotency.
- `src/use_cases/operations/lease_service.py`
  - reusable lease acquire/renew/release logic for worker execution safety.
- `src/use_cases/operations/health_service.py`
  - aggregate health view across PostgreSQL, Redis, object storage, Qdrant, and queue runtime.
- `src/adapters/database/sql/operations_models.py`
  - SQLAlchemy tables for queued jobs, worker leases, and retry attempts.
- `src/adapters/database/sql/operations_serialization.py`
  - row/domain mapping helpers.
- `src/adapters/database/sql/operations_repositories.py`
  - SQL repository implementation for queue jobs and leases.
- `src/adapters/queue/in_memory_queue.py`
  - deterministic local/test queue implementation.
- `src/adapters/queue/redis_queue.py`
  - Redis-backed queue implementation for portable runtime execution.
- `src/services/workers/worker_runtime.py`
  - orchestration loop for claiming jobs, renewing leases, running handlers, and recording outcomes.
- `src/services/workers/job_handlers.py`
  - workflow-to-handler registry for Try-On, product card, content package, pricing, and similar search.
- `src/entrypoints/runtime_dependencies.py`
  - expose queue, worker, and operations services through the composition root.
- `src/entrypoints/status_routes.py`
  - extend health output with queue/worker readiness and degraded-state reporting.
- `src/entrypoints/internal_task_routes.py`
  - optionally expose portable worker trigger endpoints if needed for controlled execution.
- `scripts/platform_foundation_smoke.py`
  - extend smoke output to include queue and worker readiness.
- `alembic/versions/20260531_000009_reliability_operations_foundation.py`
  - migration for queue and lease tables.
- `tests/test_operations_domain_models.py`
  - verify typed operations contracts.
- `tests/test_operations_sql_models.py`
  - verify SQL schema.
- `tests/test_operations_sql_repositories.py`
  - verify queue and lease persistence.
- `tests/test_dispatch_service.py`
  - verify idempotent enqueue behavior.
- `tests/test_lease_service.py`
  - verify acquire, renew, expiry, and release logic.
- `tests/test_worker_runtime.py`
  - verify worker claim, retry, and completion behavior.
- `tests/test_operations_runtime_wiring.py`
  - verify runtime dependency selection and caching.
- `tests/test_status_routes_health_runtime.py`
  - verify health payload includes worker and queue readiness.
- `tests/test_platform_foundation_smoke.py`
  - verify smoke output covers operations runtime.
- `tests/architecture/test_operations_guardrails.py`
  - enforce no heavy workflow execution inside request handlers.
- `README.md`
  - document worker topology and runtime safety expectations.
- `docs/project_description.md`
  - record the operations baseline.
- `docs/project_structure.md`
  - record queue, worker, and operations modules.
- `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`
  - mark Stage 10 planning complete.

## Task 1: Define Operations Domain Contracts

**Files:**
- Create: `src/domain/operations.py`
- Create: `tests/test_operations_domain_models.py`

- [ ] **Step 1: Write the failing domain-model tests**

```python
from src.domain.operations import QueueJobRecord, WorkerLeaseRecord


def test_queue_job_record_keeps_workflow_kind_and_idempotency_key() -> None:
    job = QueueJobRecord(
        job_id="queue_job_1",
        workflow_type="try_on",
        workflow_reference="try_on_123",
        status="queued",
        idempotency_key="try_on:try_on_123",
    )

    assert job.workflow_type == "try_on"
    assert job.idempotency_key == "try_on:try_on_123"


def test_worker_lease_record_tracks_owner_and_expiry() -> None:
    lease = WorkerLeaseRecord(
        lease_id="lease_1",
        queue_job_id="queue_job_1",
        worker_name="portable-worker",
        status="active",
        expires_at="2026-05-31T00:10:00+00:00",
    )

    assert lease.worker_name == "portable-worker"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_operations_domain_models.py -q`  
Expected: FAIL because operations domain models do not exist yet.

- [ ] **Step 3: Implement the minimal domain models**

```python
class QueueJobRecord(BaseModel):
    job_id: str
    workflow_type: str
    workflow_reference: str
    status: str
    idempotency_key: str
```

```python
class WorkerLeaseRecord(BaseModel):
    lease_id: str
    queue_job_id: str
    worker_name: str
    status: str
    expires_at: datetime
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_operations_domain_models.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/operations.py tests/test_operations_domain_models.py
git commit -m "feat: define operations domain models"
```

## Task 2: Add Queue And Lease SQL Foundation

**Files:**
- Create: `src/adapters/database/sql/operations_models.py`
- Create: `alembic/versions/20260531_000009_reliability_operations_foundation.py`
- Create: `tests/test_operations_sql_models.py`

- [ ] **Step 1: Write the failing SQL-model tests**

```python
from src.adapters.database.sql.operations_models import QueueJobRow, WorkerLeaseRow


def test_operations_sql_models_define_queue_and_lease_tables() -> None:
    assert QueueJobRow.__tablename__ == "workflow_queue_jobs"
    assert WorkerLeaseRow.__tablename__ == "worker_leases"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_operations_sql_models.py -q`  
Expected: FAIL because operations SQL models do not exist yet.

- [ ] **Step 3: Implement SQLAlchemy models and migration**

```python
class QueueJobRow(SqlBase):
    __tablename__ = "workflow_queue_jobs"
    queue_job_id = mapped_column(String(64), primary_key=True)
    workflow_type = mapped_column(String(64), nullable=False)
    workflow_reference = mapped_column(String(64), nullable=False)
    status = mapped_column(String(32), nullable=False)
    idempotency_key = mapped_column(String(255), nullable=False, unique=True)
```

```python
class WorkerLeaseRow(SqlBase):
    __tablename__ = "worker_leases"
    lease_id = mapped_column(String(64), primary_key=True)
    queue_job_id = mapped_column(ForeignKey("workflow_queue_jobs.queue_job_id", ondelete="CASCADE"), nullable=False)
    worker_name = mapped_column(String(64), nullable=False)
    status = mapped_column(String(32), nullable=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_operations_sql_models.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/operations_models.py alembic/versions/20260531_000009_reliability_operations_foundation.py tests/test_operations_sql_models.py
git commit -m "feat: add operations sql foundation"
```

## Task 3: Add Queue And Lease Repository Layer

**Files:**
- Create: `src/adapters/database/sql/operations_serialization.py`
- Create: `src/adapters/database/sql/operations_repositories.py`
- Create: `tests/test_operations_sql_repositories.py`

- [ ] **Step 1: Write the failing repository tests**

```python
async def test_operations_repository_enqueues_and_reads_queue_job() -> None:
    repository = SqlOperationsRepository(session_factory=...)
    job = await repository.enqueue_job(...)

    assert job.status == "queued"


async def test_operations_repository_claims_and_releases_worker_lease() -> None:
    repository = SqlOperationsRepository(session_factory=...)
    lease = await repository.acquire_lease(...)
    released = await repository.release_lease(lease.lease_id)

    assert released.status == "released"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_operations_sql_repositories.py -q`  
Expected: FAIL because operations repository implementation does not exist yet.

- [ ] **Step 3: Implement serialization and repository**

```python
class SqlOperationsRepository:
    async def enqueue_job(...) -> QueueJobRecord:
        ...

    async def claim_next_job(...) -> QueueJobRecord | None:
        ...

    async def acquire_lease(...) -> WorkerLeaseRecord:
        ...

    async def renew_lease(...) -> WorkerLeaseRecord:
        ...

    async def release_lease(...) -> WorkerLeaseRecord:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_operations_sql_repositories.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/operations_serialization.py src/adapters/database/sql/operations_repositories.py tests/test_operations_sql_repositories.py
git commit -m "feat: add operations sql repositories"
```

## Task 4: Add Portable Queue Adapters

**Files:**
- Create: `src/adapters/queue/in_memory_queue.py`
- Create: `src/adapters/queue/redis_queue.py`
- Create: `src/use_cases/operations/ports.py`
- Create: `tests/test_dispatch_service.py`

- [ ] **Step 1: Write the failing dispatch tests**

```python
async def test_dispatch_service_enqueues_one_idempotent_job() -> None:
    service = WorkflowDispatchService(queue=..., repository=...)
    first = await service.enqueue_workflow(...)
    second = await service.enqueue_workflow(...)

    assert first.job_id == second.job_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_dispatch_service.py -q`  
Expected: FAIL because dispatch and queue adapters do not exist yet.

- [ ] **Step 3: Implement queue ports and dispatch service**

```python
class QueuePublisherPort(Protocol):
    async def publish(self, job: QueueJobRecord) -> None:
        ...
```

```python
class WorkflowDispatchService:
    async def enqueue_workflow(...) -> QueueJobRecord:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_dispatch_service.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/queue/in_memory_queue.py src/adapters/queue/redis_queue.py src/use_cases/operations/ports.py src/use_cases/operations/dispatch_service.py tests/test_dispatch_service.py
git commit -m "feat: add portable dispatch service"
```

## Task 5: Add Lease Service And Worker Runtime

**Files:**
- Create: `src/use_cases/operations/lease_service.py`
- Create: `src/services/workers/worker_runtime.py`
- Create: `src/services/workers/job_handlers.py`
- Create: `tests/test_lease_service.py`
- Create: `tests/test_worker_runtime.py`

- [ ] **Step 1: Write the failing lease and worker tests**

```python
async def test_lease_service_renews_active_lease() -> None:
    service = WorkerLeaseService(repository=..., clock=...)
    lease = await service.acquire(...)
    renewed = await service.renew(lease.lease_id)

    assert renewed.status == "active"


async def test_worker_runtime_marks_job_completed_after_handler_success() -> None:
    runtime = WorkerRuntime(...)
    result = await runtime.run_one_cycle()

    assert result.completed_jobs == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_lease_service.py tests/test_worker_runtime.py -q`  
Expected: FAIL because lease and worker runtime do not exist yet.

- [ ] **Step 3: Implement lease safety and worker loop**

```python
class WorkerLeaseService:
    async def acquire(...) -> WorkerLeaseRecord:
        ...

    async def renew(...) -> WorkerLeaseRecord:
        ...

    async def release(...) -> WorkerLeaseRecord:
        ...
```

```python
class WorkerRuntime:
    async def run_one_cycle(self) -> WorkerCycleResult:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_lease_service.py tests/test_worker_runtime.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/operations/lease_service.py src/services/workers/worker_runtime.py src/services/workers/job_handlers.py tests/test_lease_service.py tests/test_worker_runtime.py
git commit -m "feat: add worker runtime"
```

## Task 6: Add Runtime Wiring And Health Aggregation

**Files:**
- Create: `src/use_cases/operations/health_service.py`
- Modify: `src/entrypoints/runtime_dependencies.py`
- Modify: `src/entrypoints/status_routes.py`
- Create: `tests/test_operations_runtime_wiring.py`
- Create: `tests/test_status_routes_health_runtime.py`

- [ ] **Step 1: Write the failing runtime and health tests**

```python
def test_operations_runtime_dependencies_select_portable_queue_backend(monkeypatch) -> None:
    ...


def test_health_route_reports_queue_and_worker_readiness(client) -> None:
    response = client.get("/health")
    assert "queue" in response.json()["components"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_operations_runtime_wiring.py tests/test_status_routes_health_runtime.py -q`  
Expected: FAIL because operations runtime wiring does not exist yet.

- [ ] **Step 3: Implement runtime dependencies and health aggregation**

```python
@dataclass(frozen=True)
class OperationsRuntimeDependencies:
    dispatch_service: WorkflowDispatchService
    worker_runtime: WorkerRuntime
    health_service: OperationsHealthService
```

```python
async def health_check(...) -> JSONResponse:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_operations_runtime_wiring.py tests/test_status_routes_health_runtime.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/operations/health_service.py src/entrypoints/runtime_dependencies.py src/entrypoints/status_routes.py tests/test_operations_runtime_wiring.py tests/test_status_routes_health_runtime.py
git commit -m "feat: add operations runtime health wiring"
```

## Task 7: Add Smoke Coverage, Guardrails, And Ops Docs

**Files:**
- Modify: `scripts/platform_foundation_smoke.py`
- Modify: `tests/test_platform_foundation_smoke.py`
- Create: `tests/architecture/test_operations_guardrails.py`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Write the failing smoke and guardrail tests**

```python
def test_platform_foundation_smoke_reports_queue_and_worker_components() -> None:
    ...


def test_request_routes_do_not_execute_heavy_workflow_logic_inline() -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_platform_foundation_smoke.py tests/architecture/test_operations_guardrails.py -q`  
Expected: FAIL because operations smoke coverage and guardrails do not exist yet.

- [ ] **Step 3: Implement smoke output, guardrails, and docs**

Document:

- worker topology and where heavy workflows run
- queue backend expectations
- Redis role in coordination
- PostgreSQL backup and replica assumptions
- Qdrant redundancy assumptions
- object storage durability and export expectations
- alerting and degraded-mode expectations

- [ ] **Step 4: Run final verification**

Run:

```bash
python -m pytest tests/test_operations_domain_models.py tests/test_operations_sql_models.py tests/test_operations_sql_repositories.py tests/test_dispatch_service.py tests/test_lease_service.py tests/test_worker_runtime.py tests/test_operations_runtime_wiring.py tests/test_status_routes_health_runtime.py tests/test_platform_foundation_smoke.py tests/architecture/test_operations_guardrails.py -q
python -m pytest tests/test_try_on_runtime_wiring.py tests/test_product_card_runtime_wiring.py tests/test_content_package_runtime_wiring.py tests/test_pricing_runtime_wiring.py tests/test_runtime_dependencies_container.py tests/architecture/test_billing_guardrails.py -q
```

Expected:

- all Stage 10 targeted tests PASS
- heavy workflow contours remain isolated from request handlers
- health and smoke outputs reflect queue and worker readiness

- [ ] **Step 5: Commit**

```bash
git add scripts/platform_foundation_smoke.py tests/test_platform_foundation_smoke.py tests/architecture/test_operations_guardrails.py README.md docs/project_description.md docs/project_structure.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "docs: finalize reliability operations contour"
```

## Self-Review Checklist

Spec coverage check:

- worker topology: covered by Tasks 4, 5, 6, 7
- queue and background execution: covered by Tasks 3, 4, 5
- PostgreSQL backup and replica strategy: covered by Task 7 docs
- Qdrant redundancy strategy: covered by Task 7 docs
- storage durability and export handling: covered by Task 7 docs
- observability and alerting: covered by Tasks 6 and 7
- rate limiting and abuse controls: covered by Task 7 docs plus existing regression suite

Placeholder scan:

- no `TODO`
- no `TBD`
- no unresolved file paths

Type consistency check:

- `QueueJobRecord` and `WorkerLeaseRecord` are defined before repository and worker tasks use them
- runtime wiring depends on already-defined dispatch, lease, and health services
- smoke and guardrail tasks refer only to files introduced earlier in the plan

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-reliability-operations-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
