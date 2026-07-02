# Staging Try-On Acceptance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make staging Try-On acceptance reproducible by seeding baseline wear controls and exposing actionable Quality Verifier rejection diagnostics.

**Architecture:** Baseline catalog data is delivered through Alembic, not manual DB edits. Quality rejection diagnostics stay backend-owned in `try_on_errors.details` and remain safe for API/status consumers.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy/Alembic, PostgreSQL, pytest, Firebase Hosting, Docker Compose staging runtime.

---

### Task 1: Seed Baseline Wear-Control Catalog

**Files:**
- Create: `alembic/versions/20260624_000020_seed_baseline_garment_wear_controls.py`
- Modify: `tests/test_garment_taxonomy_sql_migration.py`

- [ ] Write a failing migration test proving `000020` exists, links from `20260624_000019`, inserts baseline taxonomy items, inserts baseline controls, and deletes only seeded rows on downgrade.
- [ ] Run the migration test and confirm it fails because the migration does not exist.
- [ ] Add the Alembic migration with deterministic ids and `op.bulk_insert`.
- [ ] Run the migration test and confirm it passes.

### Task 2: Persist Quality Rejection Diagnostics

**Files:**
- Modify: `src/use_cases/try_on/workflow_execution.py`
- Modify: `tests/test_try_on_sandbox_lifecycle.py`

- [ ] Write a failing workflow test proving a failed quality result stores `quality_confidence`, `quality_checks`, and `quality_limitations` in `TryOnError.details`.
- [ ] Run the test and confirm it fails because only `verdict` is currently stored.
- [ ] Add a small serializer helper for failed quality report details.
- [ ] Run the targeted test and confirm it passes.

### Task 3: Verify, Deploy, And Repeat Acceptance

**Files:**
- Modify: `docs/01_ACTION_LOG_CHECKLIST.md`

- [ ] Run targeted backend tests for taxonomy, Try-On lifecycle, pre-generation analysis, and CORS.
- [ ] Run `compileall` and architecture guardrail.
- [ ] Deploy backend to VM.
- [ ] Verify migration head is `20260624_000020`.
- [ ] Verify `Shirt` returns seeded wear controls on staging.
- [ ] Repeat staging Try-On acceptance and record the result.
