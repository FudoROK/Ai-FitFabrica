# FitFabrica Credits And Billing Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first backend-owned credits and billing core so FitFabrica can calculate workflow cost, record durable ledger events, apply free repair and retry policy, and expose a consistent economics baseline for Try-On and B2B workflows.

**Architecture:** Keep all commercial logic in backend-owned domain and use-case layers. PostgreSQL becomes the durable source of truth for credit accounts, ledger entries, workflow pricing policies, and adjustments. Individual workflows stop inventing ad-hoc `charged_credits` decisions and instead call a central billing service that records explicit ledger events with reasons, references, and idempotent workflow keys.

**Tech Stack:** FastAPI, Python, Pydantic, SQLAlchemy, Alembic, PostgreSQL, pytest.

---

## Scope And Baseline

Current state in this worktree:

- Try-On stores `charged_credits` inside workflow events, but there is no reusable billing core.
- Product card, content package, and pricing workflows exist, but none of them persist durable credit ledger entries yet.
- No PostgreSQL tables exist yet for credit accounts, ledger events, refund events, or workflow pricing policy.
- Frontend routes exist conceptually for credits, but backend still lacks a single source of truth for balances and adjustments.

This stage builds:

- backend-owned credit accounts
- durable credit ledger entries
- workflow cost policy and lookup
- free repair / retry policy enforcement
- refund and manual adjustment recording
- reporting-ready balance and ledger-query boundaries

This stage does not yet implement:

- payment gateway integration
- fiat invoicing or tax logic
- subscription renewal automation
- admin UI

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/billing.py`
  - typed credit account, ledger event, workflow charge, refund, and balance models.
- `src/use_cases/billing/ports.py`
  - workflow-facing ports for billing repositories and policy lookup.
- `src/use_cases/billing/policy.py`
  - reusable workflow pricing and repair/retry charging rules.
- `src/use_cases/billing/service.py`
  - backend-owned billing orchestration for charge, refund, adjustment, and balance reads.
- `src/adapters/database/sql/billing_models.py`
  - SQLAlchemy tables for credit accounts, ledger events, and workflow pricing rules.
- `src/adapters/database/sql/billing_serialization.py`
  - row/domain mapping helpers.
- `src/adapters/database/sql/billing_repositories.py`
  - SQL repository implementation.
- `alembic/versions/20260531_000008_credits_billing_core.py`
  - migration for billing foundation tables.
- `src/entrypoints/runtime_dependencies.py`
  - expose billing runtime dependencies.
- `src/entrypoints/credits_routes.py`
  - FastAPI endpoints for account balance and ledger history.
- `src/use_cases/try_on/workflow_service.py`
  - replace inline cost decisions with billing-service calls.
- `src/use_cases/product_card/workflow_service.py`
  - record workflow charge events through billing core.
- `src/use_cases/content_package/workflow_service.py`
  - record workflow charge events through billing core.
- `src/use_cases/pricing/workflow_service.py`
  - record workflow charge events through billing core.
- `src/entrypoints/http_routes.py`
  - include credits router if the route is added here.
- `tests/test_billing_domain_models.py`
  - verify typed billing contracts.
- `tests/test_billing_policy.py`
  - verify workflow pricing and free repair/retry logic.
- `tests/test_billing_sql_models.py`
  - verify SQL schema.
- `tests/test_billing_sql_repositories.py`
  - verify account and ledger persistence.
- `tests/test_billing_service.py`
  - verify billing orchestration and idempotency.
- `tests/test_credits_routes.py`
  - verify balance and ledger API behavior.
- `tests/test_try_on_billing_integration.py`
  - verify Try-On charges and free repair/retry policy.
- `tests/test_b2b_billing_integration.py`
  - verify product-card, content-package, and pricing billing integration.
- `tests/architecture/test_billing_guardrails.py`
  - enforce backend-owned credits logic and prevent frontend-like cost calculations from creeping into workflow modules.
- `README.md`
  - document billing baseline.
- `docs/project_description.md`
  - record the economics foundation.
- `docs/project_structure.md`
  - record the new billing modules.
- `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`
  - mark Stage 9 planning complete.

## Task 1: Define Billing Domain Contracts

**Files:**
- Create: `src/domain/billing.py`
- Create: `tests/test_billing_domain_models.py`

- [ ] **Step 1: Write the failing domain-model tests**

```python
from src.domain.billing import CreditAccount, LedgerEvent, WorkflowChargeRequest


def test_credit_account_keeps_available_and_reserved_balances() -> None:
    account = CreditAccount(
        owner_id="user-1",
        owner_type="person",
        available_credits=120,
        reserved_credits=15,
    )

    assert account.available_credits == 120
    assert account.reserved_credits == 15


def test_workflow_charge_request_tracks_policy_and_reference() -> None:
    charge = WorkflowChargeRequest(
        owner_id="user-1",
        owner_type="person",
        workflow_type="try_on",
        workflow_reference="job-1",
        stage_name="generation_pass",
        requested_credits=12,
        charge_policy="standard",
    )

    assert charge.workflow_reference == "job-1"
    assert charge.charge_policy == "standard"


def test_ledger_event_exposes_balance_after_event() -> None:
    event = LedgerEvent(
        event_id="evt-1",
        owner_id="user-1",
        owner_type="person",
        event_type="charge",
        credits_delta=-12,
        balance_after_event=108,
        workflow_type="try_on",
        workflow_reference="job-1",
    )

    assert event.balance_after_event == 108
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_billing_domain_models.py -q`  
Expected: FAIL because billing domain models do not exist yet.

- [ ] **Step 3: Implement the minimal domain models**

```python
class CreditAccount(BaseModel):
    owner_id: str
    owner_type: Literal["person", "business"]
    available_credits: int = Field(ge=0)
    reserved_credits: int = Field(default=0, ge=0)
```

```python
class WorkflowChargeRequest(BaseModel):
    owner_id: str
    owner_type: Literal["person", "business"]
    workflow_type: str
    workflow_reference: str
    stage_name: str
    requested_credits: int = Field(ge=0)
    charge_policy: Literal["standard", "free_retry", "free_repair", "manual_adjustment"]
```

```python
class LedgerEvent(BaseModel):
    event_id: str
    owner_id: str
    owner_type: Literal["person", "business"]
    event_type: Literal["charge", "refund", "adjustment", "grant"]
    credits_delta: int
    balance_after_event: int = Field(ge=0)
    workflow_type: str | None = None
    workflow_reference: str | None = None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_billing_domain_models.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/billing.py tests/test_billing_domain_models.py
git commit -m "feat: define billing domain contracts"
```

## Task 2: Add Billing Policy Rules

**Files:**
- Create: `src/use_cases/billing/ports.py`
- Create: `src/use_cases/billing/policy.py`
- Create: `tests/test_billing_policy.py`

- [ ] **Step 1: Write the failing policy tests**

```python
from src.use_cases.billing.policy import BillingPolicyResolver


def test_billing_policy_returns_free_retry_for_system_failure() -> None:
    resolver = BillingPolicyResolver(
        workflow_base_costs={"try_on": 12},
    )

    policy = resolver.resolve_charge_policy(
        workflow_type="try_on",
        stage_name="retry_after_system_failure",
        failure_owner="system",
        recovery_kind="retry",
    )

    assert policy.charge_policy == "free_retry"
    assert policy.credits_to_charge == 0


def test_billing_policy_returns_standard_charge_for_first_successful_run() -> None:
    resolver = BillingPolicyResolver(
        workflow_base_costs={"product_card": 18},
    )

    policy = resolver.resolve_charge_policy(
        workflow_type="product_card",
        stage_name="completed",
        failure_owner=None,
        recovery_kind=None,
    )

    assert policy.charge_policy == "standard"
    assert policy.credits_to_charge == 18
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_billing_policy.py -q`  
Expected: FAIL because billing policy logic does not exist yet.

- [ ] **Step 3: Implement the minimal policy resolver**

```python
class BillingPolicyResolver:
    def __init__(self, workflow_base_costs: dict[str, int]) -> None:
        self._workflow_base_costs = workflow_base_costs

    def resolve_charge_policy(
        self,
        workflow_type: str,
        stage_name: str,
        failure_owner: str | None,
        recovery_kind: str | None,
    ) -> ResolvedBillingPolicy:
        if failure_owner == "system" and recovery_kind == "retry":
            return ResolvedBillingPolicy(charge_policy="free_retry", credits_to_charge=0)
        if failure_owner == "system" and recovery_kind == "repair":
            return ResolvedBillingPolicy(charge_policy="free_repair", credits_to_charge=0)
        return ResolvedBillingPolicy(
            charge_policy="standard",
            credits_to_charge=self._workflow_base_costs[workflow_type],
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_billing_policy.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/billing/ports.py src/use_cases/billing/policy.py tests/test_billing_policy.py
git commit -m "feat: add billing policy resolver"
```

## Task 3: Add Billing SQL Foundation

**Files:**
- Create: `src/adapters/database/sql/billing_models.py`
- Create: `alembic/versions/20260531_000008_credits_billing_core.py`
- Create: `tests/test_billing_sql_models.py`

- [ ] **Step 1: Write the failing SQL-model tests**

```python
from src.adapters.database.sql.billing_models import CreditAccountRow, CreditLedgerEventRow, WorkflowPricingRuleRow


def test_billing_sql_models_define_account_ledger_and_policy_tables() -> None:
    assert CreditAccountRow.__tablename__ == "credit_accounts"
    assert CreditLedgerEventRow.__tablename__ == "credit_ledger_events"
    assert WorkflowPricingRuleRow.__tablename__ == "workflow_pricing_rules"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_billing_sql_models.py -q`  
Expected: FAIL because billing SQL models do not exist yet.

- [ ] **Step 3: Implement SQLAlchemy models and migration**

```python
class CreditAccountRow(SqlBase):
    __tablename__ = "credit_accounts"
    account_id = mapped_column(String(64), primary_key=True)
    owner_id = mapped_column(String(64), nullable=False, index=True)
    owner_type = mapped_column(String(32), nullable=False)
    available_credits = mapped_column(Integer, nullable=False)
    reserved_credits = mapped_column(Integer, nullable=False, default=0)
```

```python
class CreditLedgerEventRow(SqlBase):
    __tablename__ = "credit_ledger_events"
    event_id = mapped_column(String(64), primary_key=True)
    account_id = mapped_column(ForeignKey("credit_accounts.account_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = mapped_column(String(32), nullable=False)
    credits_delta = mapped_column(Integer, nullable=False)
    balance_after_event = mapped_column(Integer, nullable=False)
    workflow_type = mapped_column(String(64), nullable=True)
    workflow_reference = mapped_column(String(64), nullable=True)
    idempotency_key = mapped_column(String(128), nullable=False, unique=True)
```

```python
class WorkflowPricingRuleRow(SqlBase):
    __tablename__ = "workflow_pricing_rules"
    workflow_type = mapped_column(String(64), primary_key=True)
    base_credits = mapped_column(Integer, nullable=False)
    free_retry_enabled = mapped_column(Boolean, nullable=False, default=True)
    free_repair_enabled = mapped_column(Boolean, nullable=False, default=True)
```

```python
def upgrade() -> None:
    op.create_table(...)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_billing_sql_models.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/billing_models.py alembic/versions/20260531_000008_credits_billing_core.py tests/test_billing_sql_models.py
git commit -m "feat: add billing sql foundation"
```

## Task 4: Add Billing Repository Layer

**Files:**
- Create: `src/adapters/database/sql/billing_serialization.py`
- Create: `src/adapters/database/sql/billing_repositories.py`
- Create: `tests/test_billing_sql_repositories.py`

- [ ] **Step 1: Write the failing repository tests**

```python
async def test_billing_repository_creates_account_and_appends_ledger_event() -> None:
    repository = SqlBillingRepository(session_factory=...)
    account = await repository.ensure_account(owner_id="user-1", owner_type="person")
    event = await repository.append_ledger_event(...)

    assert account.owner_id == "user-1"
    assert event.balance_after_event >= 0


async def test_billing_repository_is_idempotent_for_duplicate_event_key() -> None:
    repository = SqlBillingRepository(session_factory=...)

    first = await repository.append_ledger_event(..., idempotency_key="try-on:job-1:completed")
    second = await repository.append_ledger_event(..., idempotency_key="try-on:job-1:completed")

    assert first.event_id == second.event_id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_billing_sql_repositories.py -q`  
Expected: FAIL because billing repository implementation does not exist yet.

- [ ] **Step 3: Implement serialization and repository**

```python
class SqlBillingRepository(BillingRepository):
    async def ensure_account(self, owner_id: str, owner_type: str) -> CreditAccount:
        ...

    async def append_ledger_event(self, request: LedgerAppendRequest) -> LedgerEvent:
        ...

    async def get_balance(self, owner_id: str, owner_type: str) -> CreditAccount:
        ...

    async def list_ledger_events(self, owner_id: str, owner_type: str, limit: int = 50) -> list[LedgerEvent]:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_billing_sql_repositories.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/database/sql/billing_serialization.py src/adapters/database/sql/billing_repositories.py tests/test_billing_sql_repositories.py
git commit -m "feat: add billing sql repositories"
```

## Task 5: Add Billing Service

**Files:**
- Create: `src/use_cases/billing/service.py`
- Create: `tests/test_billing_service.py`

- [ ] **Step 1: Write the failing billing-service tests**

```python
async def test_billing_service_charges_standard_workflow_cost() -> None:
    service = BillingService(repository=..., policy_resolver=...)
    event = await service.charge_workflow(
        owner_id="user-1",
        owner_type="person",
        workflow_type="try_on",
        workflow_reference="job-1",
        stage_name="completed",
    )

    assert event.credits_delta == -12


async def test_billing_service_returns_zero_charge_for_free_retry() -> None:
    service = BillingService(repository=..., policy_resolver=...)
    event = await service.charge_workflow(
        owner_id="user-1",
        owner_type="person",
        workflow_type="try_on",
        workflow_reference="job-1",
        stage_name="retry_after_system_failure",
        failure_owner="system",
        recovery_kind="retry",
    )

    assert event.credits_delta == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_billing_service.py -q`  
Expected: FAIL because billing orchestration does not exist yet.

- [ ] **Step 3: Implement the minimal billing service**

```python
class BillingService:
    def __init__(
        self,
        repository: BillingRepository,
        policy_resolver: BillingPolicyResolver,
    ) -> None:
        self._repository = repository
        self._policy_resolver = policy_resolver

    async def charge_workflow(...) -> LedgerEvent:
        ...

    async def refund_workflow(...) -> LedgerEvent:
        ...

    async def adjust_balance(...) -> LedgerEvent:
        ...

    async def get_account_balance(...) -> CreditAccount:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_billing_service.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/billing/service.py tests/test_billing_service.py
git commit -m "feat: add billing service"
```

## Task 6: Add Credits API Surface

**Files:**
- Create: `src/entrypoints/credits_routes.py`
- Modify: `src/entrypoints/runtime_dependencies.py`
- Modify: `src/entrypoints/http_routes.py`
- Create: `tests/test_credits_routes.py`

- [ ] **Step 1: Write the failing route tests**

```python
def test_get_credits_balance_returns_backend_owned_balance(client) -> None:
    response = client.get("/api/credits/person/user-1")

    assert response.status_code == 200
    assert response.json()["available_credits"] >= 0


def test_get_credits_ledger_returns_recent_events(client) -> None:
    response = client.get("/api/credits/person/user-1/ledger")

    assert response.status_code == 200
    assert isinstance(response.json()["events"], list)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_credits_routes.py -q`  
Expected: FAIL because credits routes do not exist yet.

- [ ] **Step 3: Implement routes and runtime wiring**

```python
@router.get("/api/credits/{owner_type}/{owner_id}")
async def get_credit_balance(...) -> CreditAccount:
    ...


@router.get("/api/credits/{owner_type}/{owner_id}/ledger")
async def get_credit_ledger(...) -> CreditLedgerResponse:
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_credits_routes.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/credits_routes.py src/entrypoints/runtime_dependencies.py src/entrypoints/http_routes.py tests/test_credits_routes.py
git commit -m "feat: add credits routes"
```

## Task 7: Integrate Billing Into Workflow Services

**Files:**
- Modify: `src/use_cases/try_on/workflow_service.py`
- Modify: `src/use_cases/product_card/workflow_service.py`
- Modify: `src/use_cases/content_package/workflow_service.py`
- Modify: `src/use_cases/pricing/workflow_service.py`
- Modify: `src/entrypoints/runtime_dependencies.py`
- Create: `tests/test_try_on_billing_integration.py`
- Create: `tests/test_b2b_billing_integration.py`

- [ ] **Step 1: Write the failing integration tests**

```python
async def test_try_on_does_not_charge_for_system_retry() -> None:
    service = TryOnWorkflowService(..., billing_service=...)
    result = await service.run_retry_after_system_failure(...)

    assert result.cost_events[-1].charged_credits == 0


async def test_product_card_records_charge_through_billing_core() -> None:
    service = ProductCardWorkflowService(..., billing_service=...)
    result = await service.create_product_card(...)

    assert result.ledger_event.workflow_type == "product_card"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_billing_integration.py tests/test_b2b_billing_integration.py -q`  
Expected: FAIL because workflow services are not wired to the billing core yet.

- [ ] **Step 3: Replace inline charging decisions with billing-service calls**

```python
ledger_event = await self._billing_service.charge_workflow(
    owner_id=job.owner_id,
    owner_type=job.owner_type,
    workflow_type="try_on",
    workflow_reference=job.job_id,
    stage_name="completed",
    failure_owner=None,
    recovery_kind=None,
)
```

```python
cost_event = TryOnCostEvent(
    stage_name="completed",
    charged_credits=max(0, -ledger_event.credits_delta),
    reason=ledger_event.event_type,
)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_billing_integration.py tests/test_b2b_billing_integration.py -q`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/use_cases/try_on/workflow_service.py src/use_cases/product_card/workflow_service.py src/use_cases/content_package/workflow_service.py src/use_cases/pricing/workflow_service.py src/entrypoints/runtime_dependencies.py tests/test_try_on_billing_integration.py tests/test_b2b_billing_integration.py
git commit -m "feat: wire workflows into billing core"
```

## Task 8: Add Guardrails, Docs, And Final Verification

**Files:**
- Create: `tests/architecture/test_billing_guardrails.py`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Write the failing guardrail and documentation tests**

```python
def test_billing_guardrail_blocks_direct_credit_math_inside_routes() -> None:
    ...


def test_billing_guardrail_blocks_workflow_specific_hardcoded_pricing_tables() -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_billing_guardrails.py -q`  
Expected: FAIL because guardrails do not exist yet.

- [ ] **Step 3: Implement guardrails and update docs**

```python
DISALLOWED_PATTERNS = [
    "charged_credits=",
    "available_credits -",
    "requested_credits =",
]
```

Document:

- which workflows now call billing core
- where durable ledger truth lives
- how free repair and retry are represented
- that frontend must only display balances returned by backend

- [ ] **Step 4: Run final verification**

Run:

```bash
python -m pytest tests/test_billing_domain_models.py tests/test_billing_policy.py tests/test_billing_sql_models.py tests/test_billing_sql_repositories.py tests/test_billing_service.py tests/test_credits_routes.py tests/test_try_on_billing_integration.py tests/test_b2b_billing_integration.py tests/architecture/test_billing_guardrails.py -q
python -m pytest tests/test_try_on_workflow_service_rebase.py tests/test_product_card_workflow_service.py tests/test_content_package_workflow_service.py tests/test_pricing_workflow_service.py tests/test_runtime_dependencies_container.py -q
```

Expected:

- all Stage 9 targeted tests PASS
- billing integration does not regress existing workflow foundations

- [ ] **Step 5: Commit**

```bash
git add tests/architecture/test_billing_guardrails.py README.md docs/project_description.md docs/project_structure.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "docs: finalize billing and credits core"
```

## Self-Review Checklist

Spec coverage check:

- credit ledger: covered by Tasks 1, 3, 4, 5, 6
- workflow cost model: covered by Tasks 2, 5, 7
- free repair and retry policy: covered by Tasks 2 and 7
- refunds and adjustments: covered by Tasks 1, 4, 5
- reporting boundaries: covered by Tasks 4 and 6

Placeholder scan:

- no `TODO`
- no `TBD`
- no unresolved file paths

Type consistency check:

- `CreditAccount`, `LedgerEvent`, and `WorkflowChargeRequest` are introduced before repository and service tasks use them
- `BillingPolicyResolver` is introduced before `BillingService`
- route tasks depend on account and ledger contracts already defined above

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-credits-and-billing-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
