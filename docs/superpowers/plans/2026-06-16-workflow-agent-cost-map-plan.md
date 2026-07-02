# Workflow Agent Cost Map Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first reproducible AI FitFabrica workflow cost map, credits pricing baseline, cost estimator, and CLI report without changing production workflow charging behavior.

**Architecture:** Add a focused `src/costs` contour for provider price config, workflow step estimates, credit pricing policy, and aggregation. Agent invocation metadata is enriched centrally in `AgentInvocationService`; workflows keep depending on existing billing policy and do not import provider prices. Admin endpoints remain out of scope until admin auth is ready.

**Tech Stack:** Python, Pydantic, SQLAlchemy repository records, Markdown docs, pytest.

---

### Task 1: Provider Price Config

**Files:**
- Create: `src/costs/provider_price_config.py`
- Test: `tests/test_provider_price_config.py`

- [ ] Add tests proving Gemini model prices are versioned, sourced, and fail closed for unknown provider/model.
- [ ] Implement typed provider price records with official Google pricing source notes and effective date.
- [ ] Ensure workflow code does not need to import this config directly.

### Task 2: Workflow Cost Estimator

**Files:**
- Create: `src/costs/workflow_cost_estimator.py`
- Test: `tests/test_workflow_cost_estimator.py`

- [ ] Add tests for successful workflow cost, failed-before-generation zero credits, free repair, retry cost, and gross margin.
- [ ] Implement estimator models for agent calls, generation calls, ledger events, and workflow summary.
- [ ] Keep provider cost, internal cost, credits, revenue, and margin separate.

### Task 3: Credits Pricing Policy

**Files:**
- Create: `src/costs/credits_pricing_policy.py`
- Test: `tests/test_credits_pricing_policy.py`

- [ ] Add tests for conservative, balanced, and aggressive credit recommendations.
- [ ] Implement `1 credit = 50 KZT` baseline as a configurable policy constant.
- [ ] Keep recommendations separate from current live billing policy.

### Task 4: Agent Invocation Cost Metadata

**Files:**
- Modify: `src/domain/agent_runtime.py`
- Modify: `src/use_cases/agents/invocation_service.py`
- Test: `tests/test_agent_invocation_service.py`

- [ ] Add request-level optional `workflow_type`, `attempt_number`, `retry_reason`, and `repair_reason`.
- [ ] Enrich `cost_metadata` in `AgentInvocationService` with job/workflow/provider/model/usage/cost config fields.
- [ ] Preserve existing safe audit behavior and no raw prompt/payload persistence.

### Task 5: Docs Deliverables

**Files:**
- Create: `docs/costs/workflow_agent_cost_map_v1.md`
- Create: `docs/costs/credits_policy_v1.md`
- Create: `docs/costs/credits_pricing_table_v1.md`
- Test: `tests/test_workflow_agent_cost_map_contract.py`

- [ ] Document six workflows from the source TЗ.
- [ ] Include required table columns exactly.
- [ ] Document credits charging rules and pricing table.

### Task 6: CLI Report

**Files:**
- Create: `scripts/report_workflow_costs.py`
- Test: `tests/test_report_workflow_costs.py`

- [ ] Add JSON and Markdown output modes.
- [ ] Support `--since`, `--workflow`, and `--format`.
- [ ] Keep tests offline by using input JSON fixtures instead of real Gemini or production DB.

### Task 7: Verification

**Files:**
- Modify: `docs/tests_description.md`

- [ ] Run targeted tests for the cost contour and agent invocation service.
- [ ] Run architecture guardrails and compile checks.
- [ ] Update test documentation with the new cost-map baseline.
