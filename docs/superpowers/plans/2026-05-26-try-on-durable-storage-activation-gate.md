# Try-On Durable Storage Activation Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe activation gate for Try-On durable storage so GCS/Firestore can be enabled deliberately, with typed failures, dry-run diagnostics, docs, and no live cloud calls during normal tests.

**Architecture:** Keep the current backend-first ports/adapters design. The Try-On use case continues to persist uploads/jobs through ports; Google adapters add typed error boundaries and route mapping. Activation is controlled by backend settings and a manual smoke command; defaults stay `in_memory`.

**Tech Stack:** FastAPI, Pydantic v2, pytest, Google Cloud Storage, Firestore, `anyio.to_thread`, PowerShell-compatible verification commands.

---

## Scope Boundary

This plan may add:

- typed storage exception classes;
- adapter error wrapping for GCS and Firestore;
- route-level typed `503` mapping for storage failures;
- fake-backed tests proving failures are structured;
- a dry-run-first smoke script;
- deployment/rollback documentation.

This plan must not:

- create GCS buckets;
- create Firestore databases or collections;
- write real GCS objects during tests;
- write real Firestore documents during tests;
- call Vertex, Gemini, Imagen, or any AI generation provider;
- enable `gcs`/`firestore` defaults.

Real cloud activation is a human-owned operation after this implementation lands.

## Current Baseline

- `src/domain/try_on.py` already contains `TryOnErrorCode`, `TryOnError`, and internal `TryOnStoredInput`.
- `src/use_cases/try_on/workflow_service.py` validates uploads, saves uploaded bytes through `TryOnFileStoragePort`, saves jobs through `TryOnJobRepositoryPort`, and still uses `FakeTryOnGenerationAdapter`.
- `src/adapters/try_on/gcs_file_storage.py` uploads bytes behind `GcsTryOnFileStorage`.
- `src/adapters/try_on/firestore_repository.py` saves/loads jobs behind `FirestoreTryOnJobRepository`.
- `src/entrypoints/try_on_routes.py` chooses adapters by settings and defaults to in-memory.
- `docs/try-on-sandbox-api.md` documents that durable adapters exist but live GCS/Firestore are not used unless selected by settings.

## Files To Modify

- `src/domain/try_on.py`
- `src/adapters/try_on/gcs_file_storage.py`
- `src/adapters/try_on/firestore_repository.py`
- `src/entrypoints/try_on_routes.py`
- `docs/try-on-sandbox-api.md`

## Files To Add

- `src/use_cases/try_on/storage_errors.py`
- `scripts/try_on_storage_smoke.py`
- `docs/try-on-durable-storage-activation.md`
- `tests/test_try_on_storage_error_mapping.py`
- `tests/test_try_on_storage_smoke_script.py`

## Task 1: Add Typed Storage Error Contract

**Files:**
- Modify: `src/domain/try_on.py`
- Create: `src/use_cases/try_on/storage_errors.py`
- Test: `tests/test_try_on_storage_error_mapping.py`

- [ ] **Step 1: Write failing tests for storage error shape**

Create `tests/test_try_on_storage_error_mapping.py`:

```python
"""Tests for typed Try-On storage failure handling."""
from __future__ import annotations

from src.domain.try_on import TryOnErrorCode
from src.use_cases.try_on.storage_errors import TryOnStorageError


def test_try_on_storage_error_builds_public_safe_details() -> None:
    """Storage errors must expose backend/operation without leaking credentials or raw SDK messages."""
    error = TryOnStorageError(
        backend="gcs",
        operation="save_upload",
        public_message="Try-On storage is temporarily unavailable.",
    )

    assert error.backend == "gcs"
    assert error.operation == "save_upload"
    assert error.public_message == "Try-On storage is temporarily unavailable."
    assert error.to_try_on_error().code == TryOnErrorCode.STORAGE_UNAVAILABLE
    assert error.to_try_on_error().details == {
        "backend": "gcs",
        "operation": "save_upload",
    }
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
pytest tests/test_try_on_storage_error_mapping.py -q
```

Expected: fails because `TryOnStorageError` and `STORAGE_UNAVAILABLE` do not exist.

- [ ] **Step 3: Extend Try-On error enum**

Modify `src/domain/try_on.py` inside `TryOnErrorCode`:

```python
    STORAGE_UNAVAILABLE = "storage_unavailable"
```

- [ ] **Step 4: Add storage error helper**

Create `src/use_cases/try_on/storage_errors.py`:

```python
"""Typed storage exceptions for the Try-On workflow."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from src.domain.try_on import TryOnError, TryOnErrorCode


TryOnStorageBackend = Literal["gcs", "firestore"]
TryOnStorageOperation = Literal["save_upload", "save_job", "get_job"]


@dataclass(frozen=True)
class TryOnStorageError(Exception):
    """Public-safe exception raised when a Try-On storage adapter fails."""

    backend: TryOnStorageBackend
    operation: TryOnStorageOperation
    public_message: str

    def __post_init__(self) -> None:
        """Initialize the exception message without exposing provider internals."""
        Exception.__init__(self, self.public_message)

    def to_try_on_error(self) -> TryOnError:
        """Convert the storage failure into the public Try-On error envelope."""
        return TryOnError(
            code=TryOnErrorCode.STORAGE_UNAVAILABLE,
            message=self.public_message,
            details={
                "backend": self.backend,
                "operation": self.operation,
            },
        )
```

- [ ] **Step 5: Run test and verify pass**

Run:

```powershell
pytest tests/test_try_on_storage_error_mapping.py -q
```

Expected: `1 passed`.

## Task 2: Wrap GCS Adapter Failures

**Files:**
- Modify: `src/adapters/try_on/gcs_file_storage.py`
- Test: `tests/test_try_on_storage_error_mapping.py`

- [ ] **Step 1: Add failing GCS adapter test**

Append to `tests/test_try_on_storage_error_mapping.py`:

```python
import pytest

from src.adapters.try_on.gcs_file_storage import GcsTryOnFileStorage
from src.domain.try_on import TryOnUploadRole


class FailingGcsBlob:
    """Fake blob that raises during upload."""

    name = "try-on/uploads/job/human_photo/file.jpg"

    def upload_from_string(self, data: bytes, content_type: str) -> None:
        """Raise like a provider SDK failure without requiring live GCS."""
        raise RuntimeError("provider credential failure with internal details")


class FailingGcsBucket:
    """Fake bucket that returns a failing blob."""

    name = "fitfabrica-test-bucket"

    def blob(self, name: str) -> FailingGcsBlob:
        """Return a failing blob."""
        return FailingGcsBlob()


@pytest.mark.asyncio
async def test_gcs_adapter_wraps_provider_failures() -> None:
    """GCS provider failures must become public-safe TryOnStorageError exceptions."""
    storage = GcsTryOnFileStorage(bucket=FailingGcsBucket(), upload_prefix="try-on/uploads")

    with pytest.raises(TryOnStorageError) as exc_info:
        await storage.save_upload(
            job_id="try_on_123",
            role=TryOnUploadRole.HUMAN_PHOTO,
            filename="human.jpg",
            content_type="image/jpeg",
            payload=b"image",
            sha256_hex="a" * 64,
        )

    assert exc_info.value.backend == "gcs"
    assert exc_info.value.operation == "save_upload"
    assert "credential" not in exc_info.value.public_message.lower()
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
pytest tests/test_try_on_storage_error_mapping.py::test_gcs_adapter_wraps_provider_failures -q
```

Expected: fails because raw `RuntimeError` escapes.

- [ ] **Step 3: Wrap GCS upload exceptions**

Modify `src/adapters/try_on/gcs_file_storage.py`.

Add import:

```python
from src.use_cases.try_on.storage_errors import TryOnStorageError
```

Replace the upload call in `save_upload`:

```python
        try:
            await to_thread.run_sync(upload)
        except Exception as exc:
            raise TryOnStorageError(
                backend="gcs",
                operation="save_upload",
                public_message="Try-On upload storage is temporarily unavailable.",
            ) from exc
```

- [ ] **Step 4: Run focused GCS tests**

Run:

```powershell
pytest tests/test_try_on_gcs_file_storage.py tests/test_try_on_storage_error_mapping.py::test_gcs_adapter_wraps_provider_failures -q
```

Expected: all pass.

## Task 3: Wrap Firestore Adapter Failures

**Files:**
- Modify: `src/adapters/try_on/firestore_repository.py`
- Test: `tests/test_try_on_storage_error_mapping.py`

- [ ] **Step 1: Add failing Firestore repository tests**

Append to `tests/test_try_on_storage_error_mapping.py`:

```python
from src.adapters.try_on.firestore_repository import FirestoreTryOnJobRepository
from src.domain.try_on import TryOnJob, TryOnJobStatus


class FailingFirestoreDocument:
    """Fake document that raises during reads and writes."""

    def set(self, data: dict[str, object]) -> None:
        """Raise during save."""
        raise RuntimeError("firestore permission denied internal details")

    def get(self) -> object:
        """Raise during read."""
        raise RuntimeError("firestore deadline exceeded internal details")


class FailingFirestoreCollection:
    """Fake collection returning a failing document."""

    def document(self, document_id: str) -> FailingFirestoreDocument:
        """Return a failing document."""
        return FailingFirestoreDocument()


@pytest.mark.asyncio
async def test_firestore_repository_wraps_save_failures() -> None:
    """Firestore save failures must become public-safe TryOnStorageError exceptions."""
    repository = FirestoreTryOnJobRepository(collection=FailingFirestoreCollection())
    job = TryOnJob(job_id="try_on_123", status=TryOnJobStatus.GENERATING)

    with pytest.raises(TryOnStorageError) as exc_info:
        await repository.save(job)

    assert exc_info.value.backend == "firestore"
    assert exc_info.value.operation == "save_job"
    assert "permission" not in exc_info.value.public_message.lower()


@pytest.mark.asyncio
async def test_firestore_repository_wraps_get_failures() -> None:
    """Firestore read failures must become public-safe TryOnStorageError exceptions."""
    repository = FirestoreTryOnJobRepository(collection=FailingFirestoreCollection())

    with pytest.raises(TryOnStorageError) as exc_info:
        await repository.get("try_on_123")

    assert exc_info.value.backend == "firestore"
    assert exc_info.value.operation == "get_job"
    assert "deadline" not in exc_info.value.public_message.lower()
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
pytest tests/test_try_on_storage_error_mapping.py::test_firestore_repository_wraps_save_failures tests/test_try_on_storage_error_mapping.py::test_firestore_repository_wraps_get_failures -q
```

Expected: raw `RuntimeError` escapes.

- [ ] **Step 3: Wrap Firestore save/get exceptions**

Modify `src/adapters/try_on/firestore_repository.py`.

Add import:

```python
from src.use_cases.try_on.storage_errors import TryOnStorageError
```

Replace `save` body:

```python
        document = self._collection.document(job.job_id)
        try:
            await to_thread.run_sync(document.set, job.model_dump(mode="json"))
        except Exception as exc:
            raise TryOnStorageError(
                backend="firestore",
                operation="save_job",
                public_message="Try-On job storage is temporarily unavailable.",
            ) from exc
```

Replace first part of `get`:

```python
        document = self._collection.document(job_id)
        try:
            snapshot = await to_thread.run_sync(document.get)
        except Exception as exc:
            raise TryOnStorageError(
                backend="firestore",
                operation="get_job",
                public_message="Try-On job storage is temporarily unavailable.",
            ) from exc
```

Keep existing `snapshot.exists`, `to_dict`, and `TryOnJob.model_validate(data)` logic unchanged.

- [ ] **Step 4: Run Firestore tests**

Run:

```powershell
pytest tests/test_try_on_firestore_repository.py tests/test_try_on_storage_error_mapping.py -q
```

Expected: all pass.

## Task 4: Map Storage Failures To Typed API Responses

**Files:**
- Modify: `src/entrypoints/try_on_routes.py`
- Test: `tests/test_try_on_storage_error_mapping.py`

- [ ] **Step 1: Add route-level failure tests**

Append to `tests/test_try_on_storage_error_mapping.py`:

```python
from fastapi.testclient import TestClient

from src.main import app
from src.use_cases.try_on import storage_errors


client = TestClient(app)


class RaisingWorkflowService:
    """Service fake that raises storage failures from every public operation."""

    async def create_job(self, *args: object, **kwargs: object) -> object:
        """Raise a storage failure while creating a job."""
        raise storage_errors.TryOnStorageError(
            backend="gcs",
            operation="save_upload",
            public_message="Try-On upload storage is temporarily unavailable.",
        )

    async def get_job(self, job_id: str) -> object:
        """Raise a storage failure while reading a job."""
        raise storage_errors.TryOnStorageError(
            backend="firestore",
            operation="get_job",
            public_message="Try-On job storage is temporarily unavailable.",
        )


def test_create_job_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST must return a typed 503 instead of an unstructured server error."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.jpg", b"human-image", "image/jpeg"),
            "garment_photo": ("garment.jpg", b"garment-image", "image/jpeg"),
        },
    )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "storage_unavailable",
        "message": "Try-On upload storage is temporarily unavailable.",
        "details": {"backend": "gcs", "operation": "save_upload"},
    }


def test_status_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Status polling must return a typed 503 for storage read failures."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.get("/api/jobs/try_on_123/status")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"
    assert response.json()["error"]["details"] == {"backend": "firestore", "operation": "get_job"}


def test_result_maps_storage_failure_to_503(monkeypatch: pytest.MonkeyPatch) -> None:
    """Result polling must return a typed 503 for storage read failures."""
    from src.entrypoints import try_on_routes

    monkeypatch.setattr(try_on_routes, "_service", lambda settings: RaisingWorkflowService())

    response = client.get("/api/jobs/try_on_123/result")

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"
    assert response.json()["error"]["details"] == {"backend": "firestore", "operation": "get_job"}
```

- [ ] **Step 2: Run route failure tests and verify failure**

Run:

```powershell
pytest tests/test_try_on_storage_error_mapping.py::test_create_job_maps_storage_failure_to_503 tests/test_try_on_storage_error_mapping.py::test_status_maps_storage_failure_to_503 tests/test_try_on_storage_error_mapping.py::test_result_maps_storage_failure_to_503 -q
```

Expected: failures because routes do not catch `TryOnStorageError`.

- [ ] **Step 3: Catch storage errors in routes**

Modify `src/entrypoints/try_on_routes.py`.

Add import:

```python
from src.use_cases.try_on.storage_errors import TryOnStorageError
```

In `create_try_on_job`, add after `except TryOnValidationError`:

```python
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
```

In `get_try_on_job_status`, wrap `get_job`:

```python
    try:
        job = await _service(settings).get_job(job_id)
    except TryOnStorageError as exc:
        return _error_response(503, exc.to_try_on_error())
```

In `get_try_on_job_result`, wrap `get_job` the same way.

- [ ] **Step 4: Run route failure tests and existing lifecycle tests**

Run:

```powershell
pytest tests/test_try_on_storage_error_mapping.py tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: all pass.

## Task 5: Add Dry-Run-First Storage Smoke Script

**Files:**
- Create: `scripts/try_on_storage_smoke.py`
- Test: `tests/test_try_on_storage_smoke_script.py`

- [ ] **Step 1: Add tests for smoke script dry-run behavior**

Create `tests/test_try_on_storage_smoke_script.py`:

```python
"""Tests for the Try-On durable storage smoke script."""
from __future__ import annotations

import subprocess
import sys


def test_try_on_storage_smoke_defaults_to_dry_run() -> None:
    """The smoke script must not touch live cloud resources unless explicitly requested."""
    result = subprocess.run(
        [sys.executable, "scripts/try_on_storage_smoke.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "dry_run=true" in result.stdout
    assert "live_write_check=false" in result.stdout
    assert "No GCS or Firestore write was attempted." in result.stdout


def test_try_on_storage_smoke_requires_explicit_live_flag() -> None:
    """A live write check must require an explicit CLI flag."""
    result = subprocess.run(
        [sys.executable, "scripts/try_on_storage_smoke.py", "--live-write-check"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    assert "--confirm-live-write" in result.stderr
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
pytest tests/test_try_on_storage_smoke_script.py -q
```

Expected: fails because script does not exist.

- [ ] **Step 3: Create smoke script**

Create `scripts/try_on_storage_smoke.py`:

```python
"""Manual smoke check for Try-On durable storage settings.

Default mode is dry-run and never writes to GCS or Firestore. Live writes require
both --live-write-check and --confirm-live-write, and must only be run after the
human has approved real cloud activation.
"""
from __future__ import annotations

import argparse
import sys

from src.settings import load_settings


def _parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="Try-On durable storage smoke check.")
    parser.add_argument("--live-write-check", action="store_true", help="Run a real storage write check.")
    parser.add_argument(
        "--confirm-live-write",
        action="store_true",
        help="Confirm that live cloud writes were explicitly approved.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run a dry-run settings check or reject unsafe live execution."""
    args = _parser().parse_args(argv)
    if args.live_write_check and not args.confirm_live_write:
        print("--confirm-live-write is required with --live-write-check", file=sys.stderr)
        return 2

    settings = load_settings()
    print("try_on_storage_smoke")
    print(f"dry_run={str(not args.live_write_check).lower()}")
    print(f"live_write_check={str(args.live_write_check).lower()}")
    print(f"try_on_file_storage_backend={settings.try_on_file_storage_backend}")
    print(f"try_on_job_repository_backend={settings.try_on_job_repository_backend}")
    print(f"try_on_gcs_bucket_configured={str(settings.try_on_gcs_bucket_name is not None).lower()}")
    print(f"try_on_firestore_collection={settings.try_on_firestore_collection}")

    if not args.live_write_check:
        print("No GCS or Firestore write was attempted.")
        return 0

    print("Live write check is intentionally not implemented in this activation gate.")
    print("Create a separate approved plan before writing probe objects/documents.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run smoke script tests**

Run:

```powershell
pytest tests/test_try_on_storage_smoke_script.py -q
```

Expected: all pass.

## Task 6: Update Documentation

**Files:**
- Create: `docs/try-on-durable-storage-activation.md`
- Modify: `docs/try-on-sandbox-api.md`
- Test: `tests/test_try_on_sandbox_api_docs.py`

- [ ] **Step 1: Add docs guard**

Modify `tests/test_try_on_sandbox_api_docs.py`:

```python
ACTIVATION_DOC_PATH = Path("docs/try-on-durable-storage-activation.md")


def test_try_on_durable_storage_activation_doc_exists() -> None:
    """Durable storage activation must have an explicit operator document."""
    source = ACTIVATION_DOC_PATH.read_text(encoding="utf-8")

    required_fragments = [
        "Activation Boundary",
        "Required Environment",
        "IAM",
        "Dry Run",
        "Rollback",
        "TRY_ON_FILE_STORAGE_BACKEND=gcs",
        "TRY_ON_JOB_REPOSITORY_BACKEND=firestore",
        "No Vertex",
    ]

    for fragment in required_fragments:
        assert fragment in source
```

- [ ] **Step 2: Run docs guard and verify failure**

Run:

```powershell
pytest tests/test_try_on_sandbox_api_docs.py::test_try_on_durable_storage_activation_doc_exists -q
```

Expected: fails because activation doc does not exist.

- [ ] **Step 3: Create activation doc**

Create `docs/try-on-durable-storage-activation.md`:

```markdown
# Try-On Durable Storage Activation

## Activation Boundary

Durable storage activation only changes where Try-On uploads and job aggregates are persisted. It does not enable Vertex, Gemini, Imagen, real AI generation, credits deduction, marketplace search, repair, or retry workflows.

## Required Environment

- `TRY_ON_FILE_STORAGE_BACKEND=gcs`
- `TRY_ON_JOB_REPOSITORY_BACKEND=firestore`
- `TRY_ON_GCS_BUCKET_NAME=<approved bucket name>`
- `TRY_ON_GCS_UPLOAD_PREFIX=try-on/uploads`
- `TRY_ON_FIRESTORE_COLLECTION=try_on_jobs`

Defaults remain `in_memory`. Do not set the GCS/Firestore values in local development unless the operator is deliberately testing durable storage.

## IAM

The Cloud Run service account must have only the minimum permissions needed for the approved resources:

- write objects to the configured GCS bucket prefix;
- read/write documents in the configured Firestore collection.

Do not grant broad owner/editor roles for this activation.

## Dry Run

Run:

```powershell
python scripts/try_on_storage_smoke.py
```

Expected output includes:

```text
dry_run=true
live_write_check=false
No GCS or Firestore write was attempted.
```

## Live Write Boundary

This activation gate intentionally does not perform live write probes automatically. A real write probe requires a separate approved plan or a direct explicit operator command after bucket, Firestore, IAM, and rollback have been confirmed.

## Rollback

To roll back durable storage routing, set:

```text
TRY_ON_FILE_STORAGE_BACKEND=in_memory
TRY_ON_JOB_REPOSITORY_BACKEND=in_memory
```

Redeploy the backend with those settings. Existing Firestore/GCS data is not deleted by rollback.

## No Vertex

Durable storage activation does not call Vertex or production image generation. Try-On generation remains the sandbox fake adapter until a separate generation plan is approved.
```

- [ ] **Step 4: Update sandbox API doc**

Modify `docs/try-on-sandbox-api.md` storage section to reference the activation doc:

```markdown
See `docs/try-on-durable-storage-activation.md` for the operator checklist, IAM boundary, dry-run command, and rollback procedure.
```

- [ ] **Step 5: Run docs tests**

Run:

```powershell
pytest tests/test_try_on_sandbox_api_docs.py -q
```

Expected: all pass.

## Task 7: Verification And Commit

**Files:**
- All files changed by this plan.

- [ ] **Step 1: Run focused backend checks**

Run:

```powershell
pytest tests/test_try_on_storage_error_mapping.py tests/test_try_on_storage_smoke_script.py tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_sandbox_api_docs.py -q
```

Expected: all pass.

- [ ] **Step 2: Run architecture checks**

Run:

```powershell
pytest tests/architecture/test_http_routes_no_main_dependency.py tests/architecture/test_runtime_agents_no_side_effects.py -q
```

Expected: all pass.

- [ ] **Step 3: Run full test suite**

Run:

```powershell
pytest -q
```

Expected: all pass.

- [ ] **Step 4: Run diff whitespace check**

Run:

```powershell
git diff --check
```

Expected: no output except line-ending warnings on Windows.

- [ ] **Step 5: Commit**

Run:

```powershell
git status --short
git add src/domain/try_on.py src/use_cases/try_on/storage_errors.py src/adapters/try_on/gcs_file_storage.py src/adapters/try_on/firestore_repository.py src/entrypoints/try_on_routes.py scripts/try_on_storage_smoke.py docs/try-on-durable-storage-activation.md docs/try-on-sandbox-api.md tests/test_try_on_storage_error_mapping.py tests/test_try_on_storage_smoke_script.py tests/test_try_on_sandbox_api_docs.py
git commit -m "feat: add try-on durable storage activation gate"
```

Expected: one focused implementation commit.

## Acceptance Criteria

- Default Try-On storage remains `in_memory`.
- No tests construct live GCS or Firestore clients.
- GCS upload failures are wrapped in `TryOnStorageError`.
- Firestore save/get failures are wrapped in `TryOnStorageError`.
- POST/status/result routes return typed `503 storage_unavailable` for storage failures.
- Public error details include only `backend` and `operation`.
- Smoke script defaults to dry-run and refuses live mode without explicit confirmation.
- Smoke script still does not perform live writes in this activation gate.
- Docs include env vars, IAM boundary, dry-run command, rollback, and explicit “No Vertex”.
- Full pytest suite passes.
