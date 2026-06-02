# FitFabrica Vector Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real vector retrieval foundation on Qdrant so the backend can store, query, and filter similar garments and products behind a stable portable adapter layer.

**Architecture:** Reuse the Stage 1 Qdrant bootstrap, but extend it into a real vector contour with explicit namespaces, typed payload metadata, collection bootstrap rules, and retrieval adapters. The vector layer stays isolated from PostgreSQL business truth: PostgreSQL keeps canonical records, while Qdrant stores embeddings plus retrieval metadata for fast nearest-neighbor search and filtered similarity queries.

**Tech Stack:** FastAPI, Python, Pydantic, qdrant-client, pytest.

---

## Scope And Baseline

Current state in this worktree:

- `src/adapters/vector/qdrant_client.py` builds a shared Qdrant client.
- `src/adapters/vector/qdrant_index.py` only provides deterministic collection naming.
- `src/adapters/vector/contracts.py` only exposes a thin bootstrap contract.
- No typed vector record model exists yet.
- No query adapter exists for garment or product retrieval.
- No payload filtering or namespace ownership rules are enforced in code.

This stage does not yet build the final marketplace ranking product experience. It builds the retrieval foundation that later similar-search and recommendation flows will use.

## File Structure

New and changed files should stay focused:

- `src/domain/vector_search.py`
  - Typed vector record, filter, and retrieval result models.
- `src/adapters/vector/contracts.py`
  - Expand from bootstrap-only to retrieval-facing vector contracts.
- `src/adapters/vector/namespaces.py`
  - Centralize approved namespace names and collection configuration.
- `src/adapters/vector/qdrant_index.py`
  - Add collection specs and deterministic namespace-to-collection resolution.
- `src/adapters/vector/qdrant_bootstrapper.py`
  - Ensure collections exist with the expected vector size and distance metric.
- `src/adapters/vector/qdrant_retriever.py`
  - Provide insert/search operations for garment and product embeddings.
- `src/adapters/vector/qdrant_filters.py`
  - Map typed backend filters into Qdrant payload filter structures.
- `src/entrypoints/status_routes.py`
  - Optionally extend status payload with richer vector readiness if needed.
- `tests/test_qdrant_bootstrap.py`
  - Extend bootstrap tests beyond name generation.
- `tests/test_vector_namespaces.py`
  - Validate namespace registration and collection rules.
- `tests/test_qdrant_filters.py`
  - Validate payload filter mapping.
- `tests/test_qdrant_retriever.py`
  - Validate typed insert/search behavior with local fakes.
- `tests/architecture/test_vector_foundation_guardrails.py`
  - Enforce separation from Google-managed search assumptions.
- `README.md`
  - Document the vector foundation baseline.
- `docs/project_description.md`
  - Add a short explanation of the vector retrieval layer.
- `docs/project_structure.md`
  - Add the new vector modules.

## Task 1: Define Typed Vector Search Models

**Files:**
- Create: `src/domain/vector_search.py`
- Modify: `src/adapters/vector/contracts.py`
- Create: `tests/test_vector_namespaces.py`

- [ ] **Step 1: Write the failing model tests**

```python
from src.domain.vector_search import VectorNamespace, VectorPointRecord, VectorSearchQuery


def test_vector_point_record_models_embedding_payload_and_owner() -> None:
    record = VectorPointRecord(
        point_id="garment-1",
        namespace=VectorNamespace.GARMENTS,
        embedding=[0.1, 0.2, 0.3],
        payload={"category": "dress", "color": "black"},
        owner_id="product-123",
    )

    assert record.namespace == VectorNamespace.GARMENTS
    assert record.owner_id == "product-123"


def test_vector_query_requires_positive_limit() -> None:
    query = VectorSearchQuery(
        namespace=VectorNamespace.PRODUCTS,
        embedding=[0.1, 0.2, 0.3],
        limit=5,
    )

    assert query.limit == 5
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_vector_namespaces.py -q`
Expected: FAIL because typed vector models do not exist yet.

- [ ] **Step 3: Write the minimal models and contract expansion**

```python
class VectorNamespace(StrEnum):
    GARMENTS = "garments"
    PRODUCTS = "products"
    PERSONA_STYLE = "persona_style"
    RECOGNITION = "recognition"
```

```python
class VectorPointRecord(BaseModel):
    namespace: VectorNamespace
    point_id: str
    embedding: list[float]
    payload: dict[str, str | int | float | bool]
    owner_id: str
```

```python
class VectorRetriever(Protocol):
    def upsert_points(self, *, records: list[VectorPointRecord]) -> None: ...
    def search(self, *, query: VectorSearchQuery) -> list[VectorSearchHit]: ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_vector_namespaces.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/domain/vector_search.py src/adapters/vector/contracts.py tests/test_vector_namespaces.py
git commit -m "feat: define typed vector search models"
```

## Task 2: Lock Namespace Ownership And Collection Specs

**Files:**
- Create: `src/adapters/vector/namespaces.py`
- Modify: `src/adapters/vector/qdrant_index.py`
- Test: `tests/test_vector_namespaces.py`

- [ ] **Step 1: Write the failing namespace tests**

```python
from src.adapters.vector.namespaces import VECTOR_NAMESPACE_SPECS
from src.domain.vector_search import VectorNamespace


def test_vector_namespace_specs_define_supported_collections() -> None:
    garment_spec = VECTOR_NAMESPACE_SPECS[VectorNamespace.GARMENTS]

    assert garment_spec.vector_size == 1536
    assert garment_spec.distance == "cosine"
    assert garment_spec.collection_suffix == "garments"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_vector_namespaces.py -q`
Expected: FAIL because namespace specs do not exist.

- [ ] **Step 3: Implement namespace specs**

```python
@dataclass(frozen=True)
class VectorNamespaceSpec:
    namespace: VectorNamespace
    collection_suffix: str
    vector_size: int
    distance: str
```

```python
VECTOR_NAMESPACE_SPECS = {
    VectorNamespace.GARMENTS: VectorNamespaceSpec(...),
    VectorNamespace.PRODUCTS: VectorNamespaceSpec(...),
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_vector_namespaces.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/vector/namespaces.py src/adapters/vector/qdrant_index.py tests/test_vector_namespaces.py
git commit -m "feat: define vector namespace specs"
```

## Task 3: Implement Qdrant Collection Bootstrap Rules

**Files:**
- Create: `src/adapters/vector/qdrant_bootstrapper.py`
- Modify: `tests/test_qdrant_bootstrap.py`

- [ ] **Step 1: Write the failing bootstrap tests**

```python
from src.adapters.vector.qdrant_bootstrapper import QdrantVectorBootstrapper
from src.domain.vector_search import VectorNamespace


class FakeQdrantClient:
    def __init__(self) -> None:
        self.calls = []

    def collection_exists(self, collection_name: str) -> bool:
        self.calls.append(("exists", collection_name))
        return False

    def create_collection(self, **kwargs) -> None:
        self.calls.append(("create", kwargs))


def test_bootstrapper_creates_missing_namespace_collection() -> None:
    client = FakeQdrantClient()
    bootstrapper = QdrantVectorBootstrapper(client=client, collection_prefix="fitfabrica")

    bootstrapper.ensure_collection(namespace=VectorNamespace.GARMENTS)

    assert client.calls[0] == ("exists", "fitfabrica_garments")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_qdrant_bootstrap.py -q`
Expected: FAIL because `QdrantVectorBootstrapper` does not exist.

- [ ] **Step 3: Implement the bootstrapper**

```python
class QdrantVectorBootstrapper:
    def __init__(self, *, client: object, collection_prefix: str) -> None:
        self._client = client
        self._collection_prefix = collection_prefix

    def ensure_collection(self, *, namespace: VectorNamespace) -> None:
        spec = namespace_spec(namespace)
        collection_name = collection_name_for_namespace(
            prefix=self._collection_prefix,
            namespace=spec.collection_suffix,
        )
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_qdrant_bootstrap.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/vector/qdrant_bootstrapper.py tests/test_qdrant_bootstrap.py
git commit -m "feat: add qdrant collection bootstrapper"
```

## Task 4: Add Typed Payload Filter Mapping

**Files:**
- Create: `src/adapters/vector/qdrant_filters.py`
- Create: `tests/test_qdrant_filters.py`

- [ ] **Step 1: Write the failing filter tests**

```python
from src.adapters.vector.qdrant_filters import build_qdrant_filter
from src.domain.vector_search import VectorSearchFilter


def test_filter_builder_maps_category_brand_and_price_bounds() -> None:
    payload_filter = build_qdrant_filter(
        VectorSearchFilter(
            category="dress",
            brand="zara",
            min_price=100,
            max_price=300,
        )
    )

    assert payload_filter is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_qdrant_filters.py -q`
Expected: FAIL because the filter builder does not exist.

- [ ] **Step 3: Implement the filter builder**

```python
def build_qdrant_filter(search_filter: VectorSearchFilter | None):
    if search_filter is None:
        return None
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_qdrant_filters.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/vector/qdrant_filters.py tests/test_qdrant_filters.py
git commit -m "feat: add qdrant payload filter mapping"
```

## Task 5: Build The First Qdrant Retriever Adapter

**Files:**
- Create: `src/adapters/vector/qdrant_retriever.py`
- Create: `tests/test_qdrant_retriever.py`

- [ ] **Step 1: Write the failing retriever tests**

```python
from src.adapters.vector.qdrant_retriever import QdrantVectorRetriever
from src.domain.vector_search import VectorNamespace, VectorPointRecord, VectorSearchQuery


class FakeQdrantClient:
    ...


def test_retriever_upserts_records_into_namespace_collection() -> None:
    ...


def test_retriever_search_returns_typed_hits() -> None:
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_qdrant_retriever.py -q`
Expected: FAIL because `QdrantVectorRetriever` does not exist.

- [ ] **Step 3: Implement the retriever**

```python
class QdrantVectorRetriever(VectorRetriever):
    def upsert_points(self, *, records: list[VectorPointRecord]) -> None:
        ...

    def search(self, *, query: VectorSearchQuery) -> list[VectorSearchHit]:
        ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_qdrant_retriever.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/vector/qdrant_retriever.py tests/test_qdrant_retriever.py
git commit -m "feat: add qdrant vector retriever"
```

## Task 6: Add Vector Foundation Guardrails

**Files:**
- Create: `tests/architecture/test_vector_foundation_guardrails.py`
- Modify: `README.md`
- Modify: `docs/project_description.md`
- Modify: `docs/project_structure.md`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_vector_foundation_does_not_depend_on_google_managed_search() -> None:
    root = Path("src/adapters/vector")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "vertex ai search" not in text.lower()
        assert "discoveryengine" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_vector_foundation_guardrails.py -q`
Expected: FAIL if vector code or docs still lean on Google-managed search assumptions.

- [ ] **Step 3: Add guardrails and docs**

```markdown
- Qdrant is the active vector search baseline.
- PostgreSQL stores canonical product truth; Qdrant stores retrieval embeddings and filterable similarity metadata.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/architecture/test_vector_foundation_guardrails.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/architecture/test_vector_foundation_guardrails.py README.md docs/project_description.md docs/project_structure.md
git commit -m "docs: align vector foundation baseline"
```

## Task 7: Run Final Vector Foundation Verification

**Files:**
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Update the master plan after implementation**

```markdown
- [x] **Step 12: Implement Qdrant vector layer**
```

- [ ] **Step 2: Run targeted vector verification**

Run:
`python -m pytest tests/test_qdrant_bootstrap.py tests/test_vector_namespaces.py tests/test_qdrant_filters.py tests/test_qdrant_retriever.py tests/architecture/test_vector_foundation_guardrails.py -q`

Expected: PASS

- [ ] **Step 3: Run portable regression verification**

Run:
`python -m pytest tests/test_portable_platform_settings.py tests/test_platform_foundation_smoke.py tests/test_runtime_dependencies_container.py tests/architecture/test_portable_foundation_guardrails.py -q`

Expected: PASS

- [ ] **Step 4: Run smoke command**

Run:
`python scripts/platform_foundation_smoke.py`

Expected output includes:

```text
qdrant_backend=qdrant
```

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "chore: complete vector foundation stage"
```

## Stage Exit Criteria

This stage is complete only when:

- vector namespaces are typed and approved in code
- Qdrant collection specs are explicit
- payload filtering rules exist for similarity search
- the backend has a reusable Qdrant retriever adapter for garments and products
- vector code no longer depends on Google-managed search assumptions
- retrieval load remains isolated from PostgreSQL

## Self-Review

Spec coverage checked:

- Qdrant collection model: Tasks 1, 2, 3
- embedding ownership and namespaces: Tasks 1, 2
- payload filtering rules: Task 4
- replication and recovery assumptions: Task 3 anchors collection bootstrap behavior; deeper cluster operations remain Stage 10 ops work
- reindexing strategy: Task 2 and Task 3 establish namespace/config ownership; full reindex workflow remains a later product execution concern

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each code-bearing step includes concrete code or commands.

Type consistency checked:

- `VectorNamespace`, `VectorPointRecord`, `VectorSearchQuery`, and `VectorRetriever` are used consistently across later tasks.

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-vector-foundation-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
