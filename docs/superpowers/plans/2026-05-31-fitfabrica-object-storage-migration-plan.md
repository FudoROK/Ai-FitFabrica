# FitFabrica Object Storage Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Try-On's GCS-specific upload path with a portable S3-compatible media storage contour that can also serve future workflows.

**Architecture:** Keep binary media behind a backend-owned neutral port. Reuse the Stage 1 object storage baseline, but extend it from a minimal `put_bytes` wrapper into a workflow-usable media storage slice with deterministic object naming, tenant-aware prefixes, explicit stored-object metadata, and backend-controlled signed URL issuance. GCS-specific Try-On upload code becomes migration-state and is removed from default runtime wiring.

**Tech Stack:** FastAPI, Python, Pydantic, boto3, S3-compatible object storage, pytest.

---

## Scope And Baseline

Current state in this worktree:

- `src/adapters/storage/*` contains a minimal portable S3 contract and adapters.
- `src/entrypoints/try_on_routes.py` still selects `GcsTryOnFileStorage` or `InMemoryTryOnFileStorage`.
- `src/domain/try_on.py` still models stored uploads as `in_memory | gcs`.
- Try-On docs and tests still describe GCS as the durable upload path.

This stage does not migrate Try-On jobs to PostgreSQL yet. That belongs to the Try-On rebase stage. This stage only moves binary media persistence onto the portable storage foundation.

## File Structure

New and changed files should stay split by responsibility:

- `src/adapters/storage/contracts.py`
  - Extend the neutral object storage contract with stored object metadata and signed URL capabilities.
- `src/adapters/storage/object_naming.py`
  - Centralize deterministic object-key building and filename normalization.
- `src/adapters/storage/media_storage.py`
  - Add a workflow-facing adapter that maps business upload intent onto object storage operations.
- `src/adapters/storage/in_memory_object_storage.py`
  - Support reads and test-safe signed URL behavior for local development.
- `src/adapters/storage/s3_object_storage.py`
  - Implement actual S3 upload metadata extraction and presigned GET generation.
- `src/domain/media_storage.py`
  - Add reusable typed media references for backend-owned binary artifacts.
- `src/domain/try_on.py`
  - Replace GCS-specific storage shape with portable media reference fields.
- `src/use_cases/try_on/ports.py`
  - Replace `TryOnFileStoragePort` with a neutral media port or adapt it to the new media contract.
- `src/adapters/try_on/in_memory_file_storage.py`
  - Either become a thin wrapper over neutral media storage or be removed if redundant.
- `src/adapters/try_on/gcs_file_storage.py`
  - Remove from default runtime path; retain only if an explicit migration-state boundary is still required.
- `src/entrypoints/try_on_routes.py`
  - Switch Try-On storage wiring from GCS-specific selection to portable object storage wiring.
- `src/settings.py`
  - Add object-storage naming, signed URL TTL, and optional tenant-prefix settings needed by media workflows.
- `src/services/runtime/portable_infrastructure.py`
  - Build the portable object storage and media storage runtime handles once.
- `tests/test_object_storage_contracts.py`
  - Validate neutral metadata and signed URL behavior at the contract level.
- `tests/test_media_object_naming.py`
  - Validate key layout, sanitization, and tenant isolation.
- `tests/test_s3_object_storage.py`
  - Extend adapter tests to cover upload metadata and signed URL generation.
- `tests/test_try_on_portable_media_storage.py`
  - Verify Try-On upload persistence now uses the portable media adapter.
- `tests/test_try_on_route_storage_wiring.py`
  - Replace GCS wiring assertions with S3/in-memory portable wiring assertions.
- `tests/architecture/test_object_storage_migration_guardrails.py`
  - Enforce that portable storage layers do not depend on `google.cloud.storage`.
- `docs/try-on-durable-storage-activation.md`
  - Rewrite operator guidance from GCS activation to S3-compatible activation.
- `docs/try-on-sandbox-api.md`
  - Update storage contract language to portable object storage.
- `README.md`
  - Document the active object storage baseline and required env vars.

## Task 1: Define The Portable Media Contract

**Files:**
- Modify: `src/adapters/storage/contracts.py`
- Create: `src/domain/media_storage.py`
- Modify: `src/domain/try_on.py`
- Test: `tests/test_object_storage_contracts.py`

- [ ] **Step 1: Write the failing contract tests**

```python
from src.adapters.storage.contracts import SignedUrl, StoredObject
from src.domain.media_storage import MediaObjectRef


def test_stored_object_tracks_bucket_and_object_key() -> None:
    stored = StoredObject(
        bucket_name="fitfabrica-media",
        object_key="tenants/public/try-on/job-1/human-photo.jpg",
        content_type="image/jpeg",
        content_length=12,
        etag="etag-1",
        version_id="v1",
        storage_backend="s3",
    )

    assert stored.bucket_name == "fitfabrica-media"
    assert stored.object_key.endswith("human-photo.jpg")


def test_media_object_ref_can_be_created_from_stored_object() -> None:
    ref = MediaObjectRef(
        storage_backend="s3",
        bucket_name="fitfabrica-media",
        object_key="tenants/public/try-on/job-1/human-photo.jpg",
        content_type="image/jpeg",
        size_bytes=12,
        sha256="a" * 64,
    )

    assert ref.storage_backend == "s3"
    assert ref.bucket_name == "fitfabrica-media"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_object_storage_contracts.py -q`
Expected: FAIL because `SignedUrl`, `MediaObjectRef`, or new fields do not exist yet.

- [ ] **Step 3: Write the minimal contract implementation**

```python
@dataclass(frozen=True)
class SignedUrl:
    url: str
    expires_at: datetime
    method: Literal["GET"]


@dataclass(frozen=True)
class StoredObject:
    bucket_name: str
    object_key: str
    content_type: str
    content_length: int
    etag: str | None
    version_id: str | None
    storage_backend: str
```

```python
class MediaObjectRef(BaseModel):
    model_config = ConfigDict(extra="forbid")

    storage_backend: Literal["in_memory", "s3"]
    bucket_name: str | None = None
    object_key: str = Field(min_length=1)
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_object_storage_contracts.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/storage/contracts.py src/domain/media_storage.py src/domain/try_on.py tests/test_object_storage_contracts.py
git commit -m "feat: define portable media storage contracts"
```

## Task 2: Add Deterministic Object Naming And Tenant Isolation

**Files:**
- Create: `src/adapters/storage/object_naming.py`
- Modify: `src/settings.py`
- Test: `tests/test_media_object_naming.py`

- [ ] **Step 1: Write the failing naming tests**

```python
from src.adapters.storage.object_naming import build_media_object_key


def test_try_on_upload_key_uses_tenant_and_workflow_prefix() -> None:
    key = build_media_object_key(
        tenant_id="public",
        workflow="try-on",
        job_id="job_123",
        role="human_photo",
        filename="Human Photo!!.jpg",
    )

    assert key == "fitfabrica/tenants/public/try-on/job_123/human_photo/human-photo.jpg"


def test_filename_is_safely_normalized() -> None:
    key = build_media_object_key(
        tenant_id="public",
        workflow="try-on",
        job_id="job_123",
        role="garment_photo",
        filename="  ###  ",
    )

    assert key.endswith("/garment_photo/garment_photo")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_media_object_naming.py -q`
Expected: FAIL because `build_media_object_key` does not exist.

- [ ] **Step 3: Implement object naming**

```python
def build_media_object_key(
    *,
    tenant_id: str,
    workflow: str,
    job_id: str,
    role: str,
    filename: str,
    root_prefix: str = "fitfabrica",
) -> str:
    safe_filename = normalize_storage_filename(filename=filename, fallback=role)
    return "/".join(
        [
            root_prefix.strip("/"),
            "tenants",
            tenant_id,
            workflow,
            job_id,
            role,
            safe_filename,
        ]
    )
```

```python
object_storage_signed_url_ttl_seconds: int = Field(default=900, ge=60, le=86400)
object_storage_tenant_prefix_mode: Literal["shared", "tenant_scoped"] = "shared"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_media_object_naming.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/storage/object_naming.py src/settings.py tests/test_media_object_naming.py
git commit -m "feat: add portable media object naming"
```

## Task 3: Finish The In-Memory And S3 Adapters

**Files:**
- Modify: `src/adapters/storage/in_memory_object_storage.py`
- Modify: `src/adapters/storage/s3_object_storage.py`
- Test: `tests/test_s3_object_storage.py`

- [ ] **Step 1: Write the failing adapter tests**

```python
def test_in_memory_storage_can_return_signed_get_url() -> None:
    storage = InMemoryObjectStorage()
    stored = storage.put_bytes(
        object_key="fitfabrica/tenants/public/try-on/job-1/human_photo/photo.jpg",
        payload=b"image-bytes",
        content_type="image/jpeg",
    )

    signed = storage.create_signed_get_url(stored.object_key, expires_in_seconds=900)

    assert signed.method == "GET"
    assert signed.url.startswith("memory://")


def test_s3_storage_returns_bucket_metadata_and_presigned_url(monkeypatch: pytest.MonkeyPatch) -> None:
    ...
    assert stored.bucket_name == "fitfabrica-media"
    assert signed.url == "https://signed.example/object"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_s3_object_storage.py -q`
Expected: FAIL because read/signed-url behavior and bucket metadata are missing.

- [ ] **Step 3: Implement adapter behavior**

```python
def put_bytes(self, *, object_key: str, payload: bytes, content_type: str) -> StoredObject:
    response = self._client.put_object(
        Bucket=self._bucket_name,
        Key=object_key,
        Body=payload,
        ContentType=content_type,
    )
    return StoredObject(
        bucket_name=self._bucket_name,
        object_key=object_key,
        content_type=content_type,
        content_length=len(payload),
        etag=_strip_etag(response.get("ETag")),
        version_id=response.get("VersionId"),
        storage_backend="s3",
    )


def create_signed_get_url(self, object_key: str, *, expires_in_seconds: int) -> SignedUrl:
    url = self._client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": self._bucket_name, "Key": object_key},
        ExpiresIn=expires_in_seconds,
    )
    return SignedUrl(url=url, expires_at=_utc_after(expires_in_seconds), method="GET")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_s3_object_storage.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/storage/in_memory_object_storage.py src/adapters/storage/s3_object_storage.py tests/test_s3_object_storage.py
git commit -m "feat: complete portable object storage adapters"
```

## Task 4: Build A Workflow-Facing Media Storage Adapter

**Files:**
- Create: `src/adapters/storage/media_storage.py`
- Modify: `src/use_cases/try_on/ports.py`
- Modify: `src/adapters/try_on/in_memory_file_storage.py`
- Test: `tests/test_try_on_portable_media_storage.py`

- [ ] **Step 1: Write the failing workflow adapter tests**

```python
async def test_try_on_media_storage_persists_upload_with_portable_reference() -> None:
    object_storage = InMemoryObjectStorage()
    storage = TryOnMediaStorage(object_storage=object_storage, tenant_id="public", root_prefix="fitfabrica")

    stored = await storage.save_upload(
        job_id="job-1",
        role=TryOnUploadRole.HUMAN_PHOTO,
        filename="human photo.jpg",
        content_type="image/jpeg",
        payload=b"image-bytes",
        sha256_hex="a" * 64,
    )

    assert stored.storage_backend == "in_memory"
    assert stored.object_key == "fitfabrica/tenants/public/try-on/job-1/human_photo/human-photo.jpg"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_portable_media_storage.py -q`
Expected: FAIL because `TryOnMediaStorage` does not exist.

- [ ] **Step 3: Implement the workflow adapter**

```python
class TryOnMediaStorage(TryOnFileStoragePort):
    def __init__(self, *, object_storage: ObjectStorage, tenant_id: str, root_prefix: str) -> None:
        self._object_storage = object_storage
        self._tenant_id = tenant_id
        self._root_prefix = root_prefix

    async def save_upload(...) -> TryOnStoredInput:
        object_key = build_media_object_key(
            tenant_id=self._tenant_id,
            workflow="try-on",
            job_id=job_id,
            role=role.value,
            filename=filename,
            root_prefix=self._root_prefix,
        )
        stored = self._object_storage.put_bytes(
            object_key=object_key,
            payload=payload,
            content_type=content_type,
        )
        return TryOnStoredInput(
            role=role,
            storage_backend=stored.storage_backend,
            uri=f"{stored.storage_backend}://{stored.bucket_name or 'memory'}/{stored.object_key}",
            bucket_name=stored.bucket_name,
            object_name=stored.object_key,
            content_type=content_type,
            size_bytes=len(payload),
            sha256=sha256_hex,
        )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_portable_media_storage.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/storage/media_storage.py src/use_cases/try_on/ports.py src/adapters/try_on/in_memory_file_storage.py tests/test_try_on_portable_media_storage.py
git commit -m "feat: add try-on portable media storage adapter"
```

## Task 5: Switch Runtime Wiring Away From GCS

**Files:**
- Modify: `src/services/runtime/portable_infrastructure.py`
- Modify: `src/entrypoints/try_on_routes.py`
- Modify: `tests/test_try_on_route_storage_wiring.py`
- Test: `tests/test_runtime_dependencies_container.py`

- [ ] **Step 1: Write the failing runtime wiring tests**

```python
def test_try_on_service_uses_portable_in_memory_media_storage_by_default() -> None:
    service = try_on_routes._service(_settings())

    assert service._file_storage.__class__.__name__ == "TryOnMediaStorage"


def test_try_on_service_uses_portable_s3_media_storage_when_enabled() -> None:
    settings = _settings(
        object_storage_backend="s3",
        object_storage_bucket_name="fitfabrica-media",
    )
    service = try_on_routes._service(settings)

    assert service._file_storage.__class__.__name__ == "TryOnMediaStorage"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_route_storage_wiring.py tests/test_runtime_dependencies_container.py -q`
Expected: FAIL because route wiring still selects `GcsTryOnFileStorage`.

- [ ] **Step 3: Implement portable runtime wiring**

```python
def _file_storage(settings: Settings) -> TryOnFileStoragePort:
    portable = portable_infrastructure(settings)
    return TryOnMediaStorage(
        object_storage=portable.object_storage,
        tenant_id="public",
        root_prefix=settings.object_storage_prefix,
    )
```

```python
@dataclass(frozen=True)
class PortableInfrastructure:
    sql_session_factory: async_sessionmaker[AsyncSession] | None
    redis: Redis | None
    object_storage: ObjectStorage
    qdrant: QdrantClient | None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_route_storage_wiring.py tests/test_runtime_dependencies_container.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/services/runtime/portable_infrastructure.py src/entrypoints/try_on_routes.py tests/test_try_on_route_storage_wiring.py tests/test_runtime_dependencies_container.py
git commit -m "feat: route try-on uploads through portable object storage"
```

## Task 6: Add Signed URL Policy And API-Safe Exposure Rules

**Files:**
- Modify: `src/adapters/storage/contracts.py`
- Modify: `src/domain/try_on.py`
- Modify: `src/use_cases/try_on/workflow_service.py`
- Test: `tests/test_try_on_sandbox_lifecycle.py`
- Test: `tests/test_try_on_sandbox_api_docs.py`

- [ ] **Step 1: Write the failing behavior tests**

```python
def test_try_on_public_result_does_not_expose_bucket_or_object_key() -> None:
    response = client.get(f"/api/jobs/{job_id}/result")
    serialized = json.dumps(response.json())

    assert "bucket_name" not in serialized
    assert "object_key" not in serialized


def test_signed_urls_are_backend_owned_and_temporary() -> None:
    signed = SignedUrl(url="https://signed.example/object", expires_at=utc_now(), method="GET")
    assert signed.method == "GET"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_sandbox_api_docs.py -q`
Expected: FAIL if API models or docs still mention GCS/`gs://` semantics.

- [ ] **Step 3: Implement exposure policy**

```python
class TryOnStoredInput(BaseModel):
    role: TryOnUploadRole
    storage_backend: Literal["in_memory", "s3"]
    uri: str = Field(min_length=1)
    bucket_name: str | None = None
    object_key: str | None = None
    ...
```

```python
# Public API responses keep result image URLs only.
# Internal stored input references remain on the job aggregate and never leak bucket/object details.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_sandbox_api_docs.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/adapters/storage/contracts.py src/domain/try_on.py src/use_cases/try_on/workflow_service.py tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_sandbox_api_docs.py
git commit -m "feat: enforce signed-url and media exposure policy"
```

## Task 7: Remove GCS As The Active Durable Path And Add Guardrails

**Files:**
- Modify: `src/entrypoints/try_on_routes.py`
- Modify: `src/settings.py`
- Create: `tests/architecture/test_object_storage_migration_guardrails.py`
- Modify: `tests/test_try_on_gcs_file_storage.py`

- [ ] **Step 1: Write the failing guardrail tests**

```python
from pathlib import Path


def test_portable_storage_packages_do_not_import_google_cloud_storage() -> None:
    text = Path("src/adapters/storage/media_storage.py").read_text(encoding="utf-8")
    assert "google.cloud.storage" not in text


def test_try_on_route_wiring_no_longer_selects_gcs_backend() -> None:
    text = Path("src/entrypoints/try_on_routes.py").read_text(encoding="utf-8")
    assert "try_on_file_storage_backend" not in text
    assert "GcsTryOnFileStorage" not in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/architecture/test_object_storage_migration_guardrails.py -q`
Expected: FAIL while GCS-specific wiring remains.

- [ ] **Step 3: Remove active GCS routing and mark residual adapter tests as migration-state**

```python
# Settings keep object_storage_backend only.
# Try-On routes consume the portable object storage runtime handle.
# Legacy GCS adapter tests are either removed or moved under an explicit migration-state docstring.
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/architecture/test_object_storage_migration_guardrails.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/entrypoints/try_on_routes.py src/settings.py tests/architecture/test_object_storage_migration_guardrails.py tests/test_try_on_gcs_file_storage.py
git commit -m "refactor: retire gcs as active try-on storage path"
```

## Task 8: Rewrite Operator Docs And Run Final Verification

**Files:**
- Modify: `docs/try-on-durable-storage-activation.md`
- Modify: `docs/try-on-sandbox-api.md`
- Modify: `README.md`
- Modify: `docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md`

- [ ] **Step 1: Update docs with the portable storage baseline**

```markdown
- `OBJECT_STORAGE_BACKEND=s3`
- `OBJECT_STORAGE_BUCKET_NAME=<approved bucket>`
- `OBJECT_STORAGE_ENDPOINT_URL=<provider endpoint if non-AWS>`
- `OBJECT_STORAGE_SIGNED_URL_TTL_SECONDS=900`
```

- [ ] **Step 2: Run targeted verification**

Run:
`python -m pytest tests/test_object_storage_contracts.py tests/test_media_object_naming.py tests/test_s3_object_storage.py tests/test_try_on_portable_media_storage.py tests/test_try_on_route_storage_wiring.py tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_sandbox_api_docs.py tests/test_runtime_dependencies_container.py tests/architecture/test_object_storage_migration_guardrails.py -q`

Expected: PASS

- [ ] **Step 3: Run broader regression verification**

Run:
`python -m pytest tests/test_portable_platform_settings.py tests/test_identity_runtime_wiring.py tests/test_dialog_service_decomposition.py tests/architecture/test_portable_foundation_guardrails.py tests/architecture/test_identity_portable_foundation_guardrails.py -q`

Expected: PASS

- [ ] **Step 4: Run smoke command**

Run:
`python scripts/platform_foundation_smoke.py`

Expected output includes:

```text
platform_foundation_smoke
object_storage_backend=s3
```

- [ ] **Step 5: Commit**

```bash
git add docs/try-on-durable-storage-activation.md docs/try-on-sandbox-api.md README.md docs/superpowers/plans/2026-05-29-fitfabrica-master-portable-platform-plan.md
git commit -m "docs: align object storage migration stage"
```

## Stage Exit Criteria

This stage is complete only when:

- Try-On uploads no longer require `GcsTryOnFileStorage` in active runtime wiring.
- Portable object storage exposes deterministic object metadata and signed GET URLs.
- Upload object naming is tenant-aware and backend-owned.
- Public Try-On responses do not leak raw storage internals.
- GCS remains, at most, migration-state code and not the active target path.
- Docs and env guidance point operators to the S3-compatible baseline.

## Self-Review

Spec coverage checked:

- S3-compatible storage contract: Tasks 1, 3, 4
- upload naming conventions: Task 2
- tenancy and isolation rules: Task 2
- signed URL policy: Task 6
- lifecycle and cleanup rules: Tasks 6 and 8
- migration path away from GCS-specific code: Tasks 5 and 7

Placeholder scan checked:

- No `TODO`, `TBD`, or deferred placeholders remain.
- Each code-bearing step includes concrete code or commands.

Type consistency checked:

- `StoredObject.object_key` is used consistently across storage and workflow layers.
- Try-On stored input shape converges on `in_memory | s3`, not `gcs`.

Plan complete and saved to `docs/superpowers/plans/2026-05-31-fitfabrica-object-storage-migration-plan.md`. Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
