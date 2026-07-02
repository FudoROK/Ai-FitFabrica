# Product Card Provider-Neutral Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect Product Card generation to the canonical provider-neutral agent runtime in non-test environments.

**Architecture:** Keep `ProductCardWorkflowService` dependent only on `ProductCardGenerationPort`. Add an adapter that maps portable object-storage assets and domain metadata into `AgentInvocationService`, then maps the strict Product Card agent output back into `ProductCardDraft`.

**Tech Stack:** Python, FastAPI, Pydantic, provider-neutral agent ports, portable object storage, pytest.

---

### Task 1: Product Card Agent Adapter

**Files:**
- Create: `src/adapters/agents/product_card_generation.py`
- Create: `src/use_cases/product_card/generation_errors.py`
- Test: `tests/test_product_card_agent_generation_adapter.py`

- [ ] Write failing tests proving structured request mapping, artifact integrity metadata, result mapping, and safe invocation failure.
- [ ] Implement `ProductCardAgentGenerationAdapter` using only `AgentInvocationService` and portable `ObjectStorage`.
- [ ] Run adapter tests and confirm they pass.

### Task 2: Runtime Wiring

**Files:**
- Modify: `src/entrypoints/runtime_dependency_workflow_builders.py`
- Modify: `src/entrypoints/runtime_dependencies.py`
- Modify: `tests/test_product_card_runtime_wiring.py`

- [ ] Write failing tests proving test uses fake generation and non-test uses the canonical agent adapter.
- [ ] Pass the cached canonical invocation service into the Product Card runtime builder.
- [ ] Fail closed outside tests when the provider runtime is unavailable.
- [ ] Run runtime wiring tests and confirm they pass.

### Task 3: Provider-Neutral Guardrails and Documentation

**Files:**
- Modify: `tests/architecture/test_product_card_guardrails.py`
- Modify: `docs/current_system_full_documentation.md`
- Modify: `docs/project_structure.md`

- [ ] Add guardrails preventing Product Card workflow imports of provider SDKs and ADK agent roots.
- [ ] Document that Gemini/ADK is one replaceable provider implementation.
- [ ] Run architecture, targeted backend, frontend lint, typecheck, and build checks.
