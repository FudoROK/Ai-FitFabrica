# AI FitFabrica Identity Core Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move canonical identity resolution state from Firestore runtime adapters into PostgreSQL with explicit auditability and compatibility wiring, without breaking the existing identity resolution hot path.

**Architecture:** This stage keeps `RuntimeIdentityResolutionService` and the identity-core contracts stable while replacing the production repository implementations behind them. PostgreSQL becomes the canonical persistence layer for `persons`, `channel_identities`, `identity_bindings`, and `identity_resolution_audit`, while Firestore adapters remain only as migration-state or test-only compatibility surfaces until later stages remove them entirely.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, asyncpg, PostgreSQL, pytest.

---

## Scope Boundary

This plan covers:

- canonical PostgreSQL identity tables
- SQLAlchemy identity models and mapping code
- repository implementations for `ChannelIdentityRepository`, `LeadRepository`, and `IdentityBindingRepository`
- runtime wiring changes that make PostgreSQL the production default
- identity resolution audit records
- compatibility boundaries that isolate legacy Firestore identity adapters

This plan does not cover:

- Qdrant recognition vectors
- object storage for recognition media
- backfill of historical Firestore identity data
- Try-On workflow migration
- person-profile or recognition-event business logic beyond schema placeholders

## File Structure

### New files

- `alembic/versions/20260531_000002_identity_core_foundation.py`
- `src/adapters/database/sql/identity_models.py`
- `src/adapters/database/sql/identity_repositories.py`
- `src/adapters/database/sql/identity_audit.py`
- `tests/test_identity_sql_models.py`
- `tests/test_identity_sql_repositories.py`
- `tests/test_identity_runtime_wiring.py`
- `tests/architecture/test_identity_portable_foundation_guardrails.py`

### Modified files

- `src/adapters/database/sql/__init__.py`
- `src/identity_core/models/lead.py`
- `src/identity_core/contracts/lead_repository.py`
- `src/identity_core/services/identity_resolution.py`
- `src/identity_core/services/identity_core_runtime_repositories.py`
- `src/entrypoints/runtime_dependencies.py`
- `src/settings.py`
- `README.md`
- `docs/project_description.md`
- `docs/project_structure.md`
- `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

## Task 1: Extend Identity Contracts For Canonical Person Ownership

**Files:**
- Modify: `src/identity_core/models/lead.py`
- Modify: `src/identity_core/contracts/lead_repository.py`
- Create: `tests/test_identity_sql_models.py`

- [ ] **Step 1: Write the failing identity model tests**

```python
from __future__ import annotations

from uuid import uuid4

from src.identity_core.models.lead import LeadRecord


def test_lead_record_exposes_person_id_field() -> None:
    lead = LeadRecord(
        lead_id=uuid4(),
        person_id=uuid4(),
        lifecycle_state="active",  # type: ignore[arg-type]
        display_name=None,
        metadata={},
        created_at=None,  # type: ignore[arg-type]
        updated_at=None,  # type: ignore[arg-type]
    )
    assert lead.person_id is not None
```

- [ ] **Step 2: Run the model test to verify it fails**

Run:

```bash
python -m pytest tests/test_identity_sql_models.py -q
```

Expected:

```text
TypeError: LeadRecord.__init__() got an unexpected keyword argument 'person_id'
```

- [ ] **Step 3: Add `person_id` to the canonical lead model and contract expectations**

```python
@dataclass(slots=True, frozen=True)
class LeadRecord:
    lead_id: UUID
    person_id: UUID
    lifecycle_state: LeadLifecycleState
    display_name: str | None
    metadata: JsonMap
    created_at: datetime
    updated_at: datetime
    suspended_at: datetime | None = None
    merged_into_lead_id: UUID | None = None
```

Also update repository code paths and protocol call sites to pass `person_id` explicitly.

- [ ] **Step 4: Re-run the model test and existing identity service tests**

Run:

```bash
python -m pytest tests/test_identity_sql_models.py tests/test_identity_resolution_service.py -q
```

Expected:

```text
passed
```

## Task 2: Add Canonical PostgreSQL Identity Tables And Migration

**Files:**
- Create: `src/adapters/database/sql/identity_models.py`
- Create: `alembic/versions/20260531_000002_identity_core_foundation.py`
- Modify: `src/adapters/database/sql/__init__.py`
- Test: `tests/test_identity_sql_models.py`

- [ ] **Step 1: Write the failing SQL identity table tests**

```python
from __future__ import annotations

from src.adapters.database.sql.identity_models import (
    ChannelIdentityRow,
    IdentityBindingRow,
    PersonRow,
)


def test_identity_table_names_are_stable() -> None:
    assert PersonRow.__tablename__ == "persons"
    assert ChannelIdentityRow.__tablename__ == "channel_identities"
    assert IdentityBindingRow.__tablename__ == "identity_bindings"
```

- [ ] **Step 2: Run the SQL identity model tests and verify they fail**

Run:

```bash
python -m pytest tests/test_identity_sql_models.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'src.adapters.database.sql.identity_models'
```

- [ ] **Step 3: Implement identity SQL models**

Create models for:

- `PersonRow`
- `LeadRow`
- `ChannelIdentityRow`
- `IdentityBindingRow`
- `IdentityResolutionAuditRow`

Key constraints to include:

- unique `channel` + `external_identity`
- unique active binding per `channel_identity_id`
- foreign keys from `leads.person_id`, `channel_identities.person_id`, and `identity_bindings.*`
- timestamps and state columns stored as strings

- [ ] **Step 4: Add Alembic migration for identity foundation**

Create migration that builds:

- `persons`
- `leads`
- `channel_identities`
- `identity_bindings`
- `identity_resolution_audit`

Add indexes for:

- `channel_identities(channel, external_identity)`
- `identity_bindings(channel_identity_id, binding_state)`
- `leads(person_id)`
- `identity_resolution_audit(lead_id, created_at)`

- [ ] **Step 5: Re-run SQL identity model tests**

Run:

```bash
python -m pytest tests/test_identity_sql_models.py -q
```

Expected:

```text
passed
```

## Task 3: Add SQL Repository Implementations For Identity Core Contracts

**Files:**
- Create: `src/adapters/database/sql/identity_repositories.py`
- Test: `tests/test_identity_sql_repositories.py`

- [ ] **Step 1: Write the failing SQL repository tests**

```python
from __future__ import annotations

from src.adapters.database.sql.identity_repositories import SqlChannelIdentityRepository


def test_sql_channel_identity_repository_reports_component_name() -> None:
    repository = SqlChannelIdentityRepository(session_factory=None)
    assert repository.__class__.__name__ == "SqlChannelIdentityRepository"
```

- [ ] **Step 2: Run the SQL repository tests and verify they fail**

Run:

```bash
python -m pytest tests/test_identity_sql_repositories.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'src.adapters.database.sql.identity_repositories'
```

- [ ] **Step 3: Implement SQL repositories**

Implement:

- `SqlChannelIdentityRepository`
- `SqlLeadRepository`
- `SqlIdentityBindingRepository`

Use the existing identity-core protocol method names exactly:

- `get_or_create_channel_identity`
- `get_by_channel_external`
- `update_state`
- `create_lead`
- `get_lead_by_id`
- `update_lead`
- `lookup_lead_by_channel_identity`
- `create_binding`
- `get_active_binding_for_channel_identity`
- `revoke_binding`
- `supersede_binding`
- `list_bindings_for_lead`

- [ ] **Step 4: Add deterministic repository tests around create and lookup behavior**

Add tests that prove:

- channel identity upserts return stable rows
- first identity resolution can create person and lead ownership
- active binding lookup returns the canonical lead
- revoked bindings are no longer returned as active

- [ ] **Step 5: Run repository tests**

Run:

```bash
python -m pytest tests/test_identity_sql_repositories.py -q
```

Expected:

```text
passed
```

## Task 4: Add Identity Resolution Audit Recording

**Files:**
- Create: `src/adapters/database/sql/identity_audit.py`
- Modify: `src/identity_core/services/identity_resolution.py`
- Test: `tests/test_identity_sql_repositories.py`

- [ ] **Step 1: Write the failing audit test**

```python
from __future__ import annotations

from src.identity_core.services.identity_resolution import RuntimeIdentityResolutionResult


def test_identity_resolution_result_exposes_binding_created_flag() -> None:
    result = RuntimeIdentityResolutionResult(
        canonical_lead_id="lead-1",
        channel_identity_id="channel-1",
        channel="telegram",
        external_identity="42",
        binding_created=True,
    )
    assert result.binding_created is True
```

- [ ] **Step 2: Run the audit-facing test and verify it fails**

Run:

```bash
python -m pytest tests/test_identity_sql_repositories.py -q
```

Expected:

```text
TypeError: RuntimeIdentityResolutionResult.__init__() got an unexpected keyword argument 'binding_created'
```

- [ ] **Step 3: Add explicit audit metadata to the resolution result and recorder**

Add:

- `binding_created: bool`
- `person_created: bool`
- `lead_created: bool`

Then create a thin audit recorder that can persist one `identity_resolution_audit` row per resolution outcome.

- [ ] **Step 4: Call the audit recorder from the runtime resolution flow**

Only record:

- canonical lead id
- channel identity id
- decision mode
- creation flags
- external identity hash, never raw value

- [ ] **Step 5: Re-run identity tests**

Run:

```bash
python -m pytest tests/test_identity_resolution_service.py tests/test_identity_sql_repositories.py -q
```

Expected:

```text
passed
```

## Task 5: Switch Runtime Wiring To PostgreSQL Identity Repositories

**Files:**
- Modify: `src/entrypoints/runtime_dependencies.py`
- Modify: `src/identity_core/services/identity_core_runtime_repositories.py`
- Create: `tests/test_identity_runtime_wiring.py`

- [ ] **Step 1: Write the failing runtime wiring test**

```python
from __future__ import annotations

from types import SimpleNamespace

from src.entrypoints import runtime_dependencies as deps


def test_runtime_identity_repositories_prefer_sql_when_portable_infrastructure_exists(monkeypatch) -> None:
    settings = SimpleNamespace()
    monkeypatch.setattr(deps, "portable_infrastructure", lambda _settings: SimpleNamespace(sql_session_factory="session-factory"))
    repositories = deps.identity_runtime_repositories(settings)
    assert repositories.channel_identity_repo.__class__.__name__.startswith("Sql")
```

- [ ] **Step 2: Run the runtime wiring test and verify it fails**

Run:

```bash
python -m pytest tests/test_identity_runtime_wiring.py -q
```

Expected:

```text
AttributeError: module 'src.entrypoints.runtime_dependencies' has no attribute 'identity_runtime_repositories'
```

- [ ] **Step 3: Add an explicit identity runtime repository bundle**

Add a cached helper that returns:

- SQL repositories when `portable_infrastructure(settings).sql_session_factory` exists
- in-memory repositories in test mode if SQL is not configured
- Firestore repositories only as migration-state fallback in non-test mode

- [ ] **Step 4: Route dialog and inbound services through the new identity repository bundle**

Keep the service API unchanged. Only dependency construction should move.

- [ ] **Step 5: Re-run runtime wiring and identity service tests**

Run:

```bash
python -m pytest tests/test_identity_runtime_wiring.py tests/test_identity_resolution_service.py tests/test_runtime_dependencies_container.py -q
```

Expected:

```text
passed
```

## Task 6: Isolate Legacy Firestore Identity Adapters As Migration-State Code

**Files:**
- Modify: `src/identity_core/services/identity_core_runtime_repositories.py`
- Create: `tests/architecture/test_identity_portable_foundation_guardrails.py`

- [ ] **Step 1: Write the failing architecture guardrail test**

```python
from __future__ import annotations

from pathlib import Path


def test_identity_sql_runtime_code_does_not_import_firestore() -> None:
    text = Path("src/adapters/database/sql/identity_repositories.py").read_text(encoding="utf-8").lower()
    assert "firestore" not in text
```

- [ ] **Step 2: Run the guardrail test and verify it fails if SQL code leaks Firestore terms**

Run:

```bash
python -m pytest tests/architecture/test_identity_portable_foundation_guardrails.py -q
```

Expected:

```text
passed
```

If it fails, remove all Firestore imports from SQL identity modules before continuing.

- [ ] **Step 3: Mark Firestore identity repositories as migration-state only**

Add module docstrings and comments clarifying:

- not target baseline
- temporary compatibility fallback
- no new feature work should extend these adapters

- [ ] **Step 4: Re-run architecture guardrails**

Run:

```bash
python -m pytest tests/architecture/test_identity_portable_foundation_guardrails.py tests/architecture/test_identity_resolution_step13_guardrails.py -q
```

Expected:

```text
passed
```

## Task 7: Final Verification And Documentation Alignment

**Files:**
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Update docs to reference the new identity runtime surfaces**

Document:

- `src/adapters/database/sql/identity_models.py`
- `src/adapters/database/sql/identity_repositories.py`
- `src/adapters/database/sql/identity_audit.py`
- `src/entrypoints/runtime_dependencies.py`

- [ ] **Step 2: Mark the identity migration plan as written in the master plan**

Add this line under Stage 2:

```md
- detailed plan: `docs/superpowers/plans/2026-05-31-fitfabrica-identity-core-migration-plan.md`
```

- [ ] **Step 3: Run the full identity migration verification set**

Run:

```bash
python -m pytest \
  tests/test_identity_sql_models.py \
  tests/test_identity_sql_repositories.py \
  tests/test_identity_runtime_wiring.py \
  tests/test_identity_resolution_service.py \
  tests/test_runtime_dependencies_container.py \
  tests/architecture/test_identity_portable_foundation_guardrails.py \
  tests/architecture/test_identity_resolution_step13_guardrails.py -q
```

Expected:

```text
passed
```

## Self-Review

Spec coverage check:

- canonical PostgreSQL identity records: covered in Task 2
- replacement of Firestore runtime identity repositories: covered in Task 5 and Task 6
- auditability: covered in Task 4
- transactional identity constraints: covered in Task 2 and Task 3
- compatibility boundaries: covered in Task 5 and Task 6

Placeholder scan:

- no `TODO`
- no `TBD`
- no “implement later” placeholders

Type consistency check:

- repository protocol names match current identity-core contracts
- `person_id` is introduced as the stable ownership link between `persons` and `leads`
- runtime wiring names stay consistent with `portable_infrastructure`

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-identity-core-migration-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
