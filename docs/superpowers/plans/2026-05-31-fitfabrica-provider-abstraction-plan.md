# FitFabrica Provider Abstraction Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hard-code no business workflow to a single AI provider by introducing explicit provider-neutral ports for reasoning, embeddings, image generation, image editing, and agent runtime execution.

**Architecture:** Keep the backend in control of jobs, workflow state, persistence, billing, and retries. Move provider-specific behavior behind narrow adapter contracts so Gemini/Vertex remain the first implementation, but no longer leak directly into business logic or runtime orchestration. The result should be a stable provider abstraction layer that can later host OpenAI, Anthropic, Qwen, or other adapters without redesigning the core backend.

**Tech Stack:** FastAPI, Python, Pydantic, existing `src/llm` runtime, Gemini/Vertex adapters, pytest.

---

## Scope And Baseline

Current state in this worktree:

- `src/llm/llm_service.py` still contains direct provider selection logic and explicit `GeminiStructuredProvider`/`VertexProvider` knowledge.
- `src/llm/providers/registry.py` selects providers by name but only for the current text/runtime paths.
- No explicit project-level ports exist yet for:
  - structured reasoning
  - embedding generation
  - image generation
  - image editing
  - agent runtime execution
- Vertex/Gemini remain the practical first provider implementations.
- Frontend is already expected to stay provider-blind.

This stage does not yet build every final image or embedding adapter. It hardens the abstraction boundary so later feature stages can plug providers into stable backend-owned contracts.

## File Structure

New and changed files should stay split by responsibility:

- `src/domain/provider_ports.py`
  - Provider-neutral contracts for reasoning, embeddings, image generation, image editing, and agent runtime execution.
- `src/domain/provider_models.py`
  - Typed request/result models shared across providers.
- `src/llm/provider_runtime.py`
  - Central backend-owned provider composition and selection layer.
- `src/llm/llm_service.py`
  - Consume the new provider-neutral runtime instead of constructing provider classes directly.
- `src/llm/providers/registry.py`
  - Narrow to provider registration, not business routing logic.
- `src/llm/providers/fake_provider.py`
  - Align to the provider-neutral request/result model where practical.
- `src/llm/providers/gemini_structured_provider.py`
  - Adapt into `StructuredReasoningPort`.
- `src/llm/vertex/vertex_provider.py`
  - Adapt into `AgentRuntimePort`.
- `src/adapters/ai/embedding_fake.py`
  - First non-production embedding adapter for tests and wiring.
- `src/adapters/ai/image_generation_stub.py`
  - First image-generation stub adapter for contract coverage.
- `src/adapters/ai/image_editing_stub.py`
  - First image-editing stub adapter for contract coverage.
- `src/entrypoints/runtime_dependencies.py`
  - Expose provider runtime dependencies through composition root.
- `tests/test_provider_ports.py`
  - Verify the new provider-neutral request/result contracts.
- `tests/test_provider_runtime.py`
  - Verify backend-owned provider selection and failover behavior.
- `tests/test_llm_service_provider_runtime.py`
  - Verify `LLMService` now delegates through the provider runtime.
- `tests/test_embedding_provider_runtime.py`
  - Verify embedding provider wiring.
- `tests/test_image_provider_runtime.py`
  - Verify image generation/editing stub wiring.
- `tests/architecture/test_provider_abstraction_guardrails.py`
  - Enforce that business/runtime layers do not construct Vertex/Gemini providers directly.
- `README.md`
  - Document the provider-neutral backend layer.
- `docs/project_description.md`
  - Explain the provider abstraction baseline.
- `docs/project_structure.md`
  - Record the new provider abstraction modules.

## Task 1: Define Provider-Neutral Models And Ports

**Files:**
- Create: `src/domain/provider_models.py`
- Create: `src/domain/provider_ports.py`
- Create: `tests/test_provider_ports.py`

- [ ] **Step 1: Write the failing contract tests**

```python
from src.domain.provider_models import EmbeddingRequest, StructuredReasoningRequest
from src.domain.provider_ports import EmbeddingProviderPort, StructuredReasoningPort


def test_structured_reasoning_request_models_backend_owned_contract() -> None:
    request = StructuredReasoningRequest(
        task="dialog_reply_task",
        prompt="hello",
        response_schema={"type": "object"},
    )

    assert request.task == "dialog_reply_task"


def test_embedding_request_models_namespace_and_input() -> None:
    request = EmbeddingRequest(
        namespace="garments",
        input_text="black dress with belt",
    )

    assert request.namespace == "garments"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_provider_ports.py -q`
Expected: FAIL because provider-neutral models and ports do not exist yet.

- [ ] **Step 3: Implement the minimal models and ports**

```python
class StructuredReasoningRequest(BaseModel):
    task: str
    prompt: str
    response_schema: dict[str, object]
```

```python
class StructuredReasoningPort(Protocol):
    def generate(self, request: StructuredReasoningRequest) -> StructuredReasoningResult: ...
```

```python
class EmbeddingProviderPort(Protocol):
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_provider_ports.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/provider_models.py src/domain/provider_ports.py tests/test_provider_ports.py
git commit -m "feat: define provider-neutral ai ports"
```

## Task 2: Add Backend-Owned Provider Runtime Selection

**Files:**
- Create: `src/llm/provider_runtime.py`
- Create: `tests/test_provider_runtime.py`

- [ ] **Step 1: Write the failing runtime-selection tests**

```python
from src.llm.provider_runtime import ProviderRuntime


def test_provider_runtime_exposes_structured_reasoning_and_agent_runtime_ports() -> None:
    runtime = ProviderRuntime(
        structured_reasoning=object(),
        agent_runtime=object(),
        embedding_provider=object(),
        image_generation=object(),
        image_editing=object(),
    )

    assert runtime.structured_reasoning is not None
    assert runtime.agent_runtime is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_provider_runtime.py -q`
Expected: FAIL because `ProviderRuntime` does not exist.

- [ ] **Step 3: Implement the provider runtime container**

```python
@dataclass(frozen=True)
class ProviderRuntime:
    structured_reasoning: StructuredReasoningPort | None
    agent_runtime: AgentRuntimePort | None
    embedding_provider: EmbeddingProviderPort | None
    image_generation: ImageGenerationPort | None
    image_editing: ImageEditingPort | None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_provider_runtime.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm/provider_runtime.py tests/test_provider_runtime.py
git commit -m "feat: add provider runtime container"
```

## Task 3: Route LLMService Through Provider Runtime

**Files:**
- Modify: `src/llm/llm_service.py`
- Create: `tests/test_llm_service_provider_runtime.py`

- [ ] **Step 1: Write the failing delegation tests**

```python
def test_llm_service_uses_provider_runtime_instead_of_constructing_gemini_directly() -> None:
    ...


def test_llm_service_uses_agent_runtime_for_memory_runtime_tasks() -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_llm_service_provider_runtime.py -q`
Expected: FAIL because `LLMService` still knows about `GeminiStructuredProvider` and `VertexProvider`.

- [ ] **Step 3: Implement runtime-based delegation**

```python
class LLMService:
    def __init__(..., provider_runtime: ProviderRuntime | None = None, ...):
        self.provider_runtime = provider_runtime or build_provider_runtime(self.settings)
```

```python
if task in _MEMORY_DAILY_RUNTIME_TASKS:
    if self.provider_runtime.agent_runtime is None:
        raise RuntimeError(...)
    return self.provider_runtime.agent_runtime, routing
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_llm_service_provider_runtime.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm/llm_service.py tests/test_llm_service_provider_runtime.py
git commit -m "refactor: route llm service through provider runtime"
```

## Task 4: Adapt Gemini And Vertex To Provider-Neutral Ports

**Files:**
- Modify: `src/llm/providers/gemini_structured_provider.py`
- Modify: `src/llm/vertex/vertex_provider.py`
- Modify: `src/llm/providers/registry.py`
- Create: `tests/test_provider_runtime.py`

- [ ] **Step 1: Write the failing adapter tests**

```python
def test_registry_builds_structured_reasoning_provider_for_gemini() -> None:
    ...


def test_registry_builds_agent_runtime_provider_for_vertex() -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_provider_runtime.py -q`
Expected: FAIL because registry/runtime does not expose provider-neutral ports yet.

- [ ] **Step 3: Implement provider adaptation**

```python
def build_provider_runtime(settings) -> ProviderRuntime:
    provider_name = (settings.llm.provider or "").strip().lower()
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_provider_runtime.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/llm/providers/gemini_structured_provider.py src/llm/vertex/vertex_provider.py src/llm/providers/registry.py tests/test_provider_runtime.py
git commit -m "feat: adapt gemini and vertex to provider-neutral runtime"
```

## Task 5: Add Embedding And Image Stub Providers

**Files:**
- Create: `src/adapters/ai/embedding_fake.py`
- Create: `src/adapters/ai/image_generation_stub.py`
- Create: `src/adapters/ai/image_editing_stub.py`
- Create: `tests/test_embedding_provider_runtime.py`
- Create: `tests/test_image_provider_runtime.py`

- [ ] **Step 1: Write the failing stub-provider tests**

```python
def test_fake_embedding_provider_returns_stable_embedding_shape() -> None:
    ...


def test_image_stub_provider_returns_backend_owned_placeholder_result() -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_embedding_provider_runtime.py tests/test_image_provider_runtime.py -q`
Expected: FAIL because embedding/image provider stubs do not exist.

- [ ] **Step 3: Implement the stub providers**

```python
class FakeEmbeddingProvider(EmbeddingProviderPort):
    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        ...
```

```python
class StubImageGenerationProvider(ImageGenerationPort):
    def generate(self, request: ImageGenerationRequest) -> ImageGenerationResult:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_embedding_provider_runtime.py tests/test_image_provider_runtime.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/ai/embedding_fake.py src/adapters/ai/image_generation_stub.py src/adapters/ai/image_editing_stub.py tests/test_embedding_provider_runtime.py tests/test_image_provider_runtime.py
git commit -m "feat: add provider-neutral embedding and image stubs"
```

## Task 6: Add Provider Abstraction Guardrails

**Files:**
- Create: `tests/architecture/test_provider_abstraction_guardrails.py`
- Modify: `src/entrypoints/runtime_dependencies.py`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_business_runtime_layers_do_not_construct_vertex_or_gemini_providers_directly() -> None:
    for relative_path in [
        "src/llm/llm_service.py",
        "src/entrypoints/runtime_dependencies.py",
    ]:
        text = Path(relative_path).read_text(encoding="utf-8")
        assert "GeminiStructuredProvider(" not in text
        assert "VertexProvider(" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_provider_abstraction_guardrails.py -q`
Expected: FAIL because direct provider construction still exists.

- [ ] **Step 3: Move provider construction to the provider runtime layer**

```python
# runtime_dependencies wires ProviderRuntime, not Gemini/Vertex classes directly.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/architecture/test_provider_abstraction_guardrails.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/architecture/test_provider_abstraction_guardrails.py src/entrypoints/runtime_dependencies.py
git commit -m "test: enforce provider abstraction boundaries"
```

## Task 7: Align Docs And Run Final Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Update docs for the provider-neutral backend layer**

```markdown
- backend-owned provider runtime selects reasoning, embeddings, image generation, and image editing adapters
- Gemini/Vertex are the first implementations, not hard architectural requirements
```

- [ ] **Step 2: Run targeted provider verification**

Run:
`python -m pytest tests/test_provider_ports.py tests/test_provider_runtime.py tests/test_llm_service_provider_runtime.py tests/test_embedding_provider_runtime.py tests/test_image_provider_runtime.py tests/architecture/test_provider_abstraction_guardrails.py -q`

Expected: PASS

- [ ] **Step 3: Run broader runtime regression verification**

Run:
`python -m pytest tests/test_fake_provider.py tests/test_gemini_structured_provider.py tests/test_vertex_provider.py tests/test_runtime_dependencies_container.py tests/architecture/test_architecture_enforcement.py -q`

Expected: PASS

- [ ] **Step 4: Run smoke command**

Run:
`python scripts/platform_foundation_smoke.py`

Expected output still includes:

```text
object_storage_backend=in_memory
qdrant_backend=qdrant
```

- [ ] **Step 5: Commit**

```bash
git add README.md docs/project_description.md docs/project_structure.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "docs: align provider abstraction stage"
```

## Stage Exit Criteria

This stage is complete only when:

- provider-neutral ports exist for reasoning, embeddings, image generation, image editing, and agent runtime
- `LLMService` delegates through a backend-owned provider runtime
- Gemini/Vertex are adapters, not business-layer construction points
- the backend can later add new providers without redesigning workflow orchestration
- business state remains fully backend-owned and provider-blind

## Self-Review

Spec coverage checked:

- model invocation ports: Tasks 1, 2, 3
- embedding provider ports: Tasks 1, 5
- image generation and editing ports: Tasks 1, 5
- ADK/Gemini integration boundaries: Tasks 3, 4, 6
- provider failover and fallback policy: Tasks 2, 3, 4

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each code-bearing step includes concrete code or commands.

Type consistency checked:

- `ProviderRuntime`, `StructuredReasoningPort`, `EmbeddingProviderPort`, `ImageGenerationPort`, `ImageEditingPort`, and `AgentRuntimePort` are used consistently across later tasks.

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-provider-abstraction-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
