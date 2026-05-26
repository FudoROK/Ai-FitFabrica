# Try-On Durable Storage Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to execute this plan.

**Goal:** Add the first durable storage foundation for Try-On sandbox jobs and uploaded files behind backend ports, while keeping the current public API contract stable and keeping local/test execution on in-memory adapters by default.

**Scope boundary:** This plan may add GCS and Firestore adapter code, settings, and fake-backed tests. It must not create buckets, write real GCS objects, write real Firestore documents, call Vertex, or turn durable adapters on by default. Real Google resource activation requires a separate explicit plan and approval.

**Architecture:** Backend-first hexagonal architecture. FastAPI routes only receive DTO/files and call the use case. The use case owns validation, job creation, storage persistence, and repository persistence through ports. Adapters implement Google-specific behavior behind those ports. Frontend remains a thin client and is not changed in this cycle.

**Current baseline:**
- `src/domain/try_on.py` contains strict Pydantic job/result/status models.
- `src/use_cases/try_on/workflow_service.py` validates upload bytes, creates job IDs, runs fake generation, and persists jobs through `TryOnJobRepositoryPort`.
- `src/use_cases/try_on/ports.py` currently exposes job repository and generation ports only.
- `src/adapters/try_on/in_memory_repository.py` is the only job repository.
- `src/entrypoints/try_on_routes.py` wires the in-memory repository and fake generation adapter.
- `requirements.txt` already contains `google-cloud-firestore==2.21.0` and does not contain `google-cloud-storage`.

## Desired Behavior

After implementation:

1. Existing Try-On API behavior remains compatible:
   - `POST /api/try-on/jobs`
   - `GET /api/jobs/{job_id}/status`
   - `GET /api/jobs/{job_id}/result`
2. Local/test default remains non-durable:
   - uploaded bytes are stored by an in-memory file storage adapter;
   - jobs are stored by the existing in-memory repository;
   - no Google clients are constructed unless settings explicitly select Google-backed adapters.
3. Durable adapter code exists behind explicit settings:
   - `try_on_file_storage_backend=gcs`
   - `try_on_job_repository_backend=firestore`
4. Uploaded file persistence is represented in backend-owned job data without exposing signed URLs or secrets in the public response.
5. Tests verify storage, repository serialization, settings validation, and route wiring without live GCS or Firestore.

## Files To Modify

- `requirements.txt`
- `src/domain/try_on.py`
- `src/settings.py`
- `src/use_cases/try_on/ports.py`
- `src/use_cases/try_on/workflow_service.py`
- `src/entrypoints/try_on_routes.py`
- `docs/try-on-sandbox-api.md`

## Files To Add

- `src/adapters/try_on/in_memory_file_storage.py`
- `src/adapters/try_on/gcs_file_storage.py`
- `src/adapters/try_on/firestore_repository.py`
- `tests/test_try_on_file_storage_workflow.py`
- `tests/test_try_on_firestore_repository.py`
- `tests/test_try_on_gcs_file_storage.py`
- `tests/test_try_on_storage_settings.py`
- `tests/test_try_on_route_storage_wiring.py`

## Implementation Tasks

### Task 1: Add tests for default storage settings

Create `tests/test_try_on_storage_settings.py` first.

Test cases:

```python
"""Settings tests for Try-On storage adapter selection."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.settings import Settings


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "gcp_project_id": "test-project",
        "pubsub_topic_agent_jobs": "agent-jobs",
    }
    values.update(overrides)
    return Settings(**values)


def test_try_on_storage_defaults_to_in_memory_adapters() -> None:
    """Local settings must not opt into cloud-backed Try-On storage."""
    settings = _settings()

    assert settings.try_on_file_storage_backend == "in_memory"
    assert settings.try_on_job_repository_backend == "in_memory"
    assert settings.try_on_gcs_bucket_name is None
    assert settings.try_on_gcs_upload_prefix == "try-on/uploads"
    assert settings.try_on_firestore_collection == "try_on_jobs"


def test_gcs_storage_requires_bucket_name() -> None:
    """Selecting GCS without a bucket must fail during settings validation."""
    with pytest.raises(ValidationError, match="try_on_gcs_bucket_name"):
        _settings(try_on_file_storage_backend="gcs")


def test_firestore_repository_requires_collection_name() -> None:
    """Selecting Firestore without a collection must fail during settings validation."""
    with pytest.raises(ValidationError, match="try_on_firestore_collection"):
        _settings(
            try_on_job_repository_backend="firestore",
            try_on_firestore_collection="",
        )
```

Run and confirm failure before implementation:

```powershell
pytest tests/test_try_on_storage_settings.py -q
```

Expected initial result: fails because the settings fields do not exist.

### Task 2: Implement storage settings

Modify `src/settings.py`.

Add strict literal settings:

```python
from typing import Literal
```

Add fields to `Settings`:

```python
try_on_file_storage_backend: Literal["in_memory", "gcs"] = "in_memory"
try_on_job_repository_backend: Literal["in_memory", "firestore"] = "in_memory"
try_on_gcs_bucket_name: str | None = None
try_on_gcs_upload_prefix: str = "try-on/uploads"
try_on_firestore_collection: str = "try_on_jobs"
```

Add a model validator:

```python
@model_validator(mode="after")
def _validate_try_on_storage_settings(self) -> Settings:
    """Validate Try-On storage adapter settings before app startup."""
    if self.try_on_file_storage_backend == "gcs" and not self.try_on_gcs_bucket_name:
        raise ValueError("try_on_gcs_bucket_name is required when try_on_file_storage_backend is gcs")
    if self.try_on_job_repository_backend == "firestore" and not self.try_on_firestore_collection:
        raise ValueError(
            "try_on_firestore_collection is required when try_on_job_repository_backend is firestore"
        )
    if not self.try_on_gcs_upload_prefix.strip("/"):
        raise ValueError("try_on_gcs_upload_prefix must contain at least one path segment")
    return self
```

If `model_validator` is not imported yet, import it from Pydantic.

Run:

```powershell
pytest tests/test_try_on_storage_settings.py -q
```

Expected result: pass.

### Task 3: Add domain model for stored upload references

Modify `src/domain/try_on.py`.

Add a backend-owned stored upload model:

```python
class TryOnStoredInput(BaseModel):
    """Backend-owned storage reference for a persisted Try-On input file."""

    model_config = ConfigDict(extra="forbid")

    role: TryOnUploadRole
    storage_backend: Literal["in_memory", "gcs"]
    uri: str = Field(min_length=1)
    bucket_name: str | None = None
    object_name: str | None = None
    content_type: str = Field(min_length=1)
    size_bytes: int = Field(ge=1)
    sha256: str = Field(min_length=64, max_length=64)
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("sha256")
    @classmethod
    def _validate_sha256_hex(cls, value: str) -> str:
        """Require a full SHA-256 digest encoded as 64 hexadecimal characters."""
        if not all(char in "0123456789abcdefABCDEF" for char in value):
            raise ValueError("sha256 must be 64 hexadecimal characters")
        return value
```

Add the field to `TryOnJob`:

```python
stored_inputs: list[TryOnStoredInput] = Field(default_factory=list)
```

Do not add `stored_inputs` to `TryOnJobCreatedResponse`, `TryOnJobStatusResponse`, or `TryOnResultResponse`. Stored object references are internal backend state, not public API data.

### Task 4: Add file storage port

Modify `src/use_cases/try_on/ports.py`.

Import `TryOnStoredInput` and `TryOnUploadRole`.

Add:

```python
class TryOnFileStoragePort(Protocol):
    """Port for persisting validated Try-On upload bytes."""

    async def save_upload(
        self,
        *,
        job_id: str,
        role: TryOnUploadRole,
        filename: str,
        content_type: str,
        payload: bytes,
        sha256_hex: str,
    ) -> TryOnStoredInput:
        """Persist upload bytes and return a backend-owned storage reference."""
        ...
```

### Task 5: Add failing workflow test for stored uploads

Create `tests/test_try_on_file_storage_workflow.py`.

```python
"""Workflow tests for persisted Try-On upload references."""
from __future__ import annotations

from io import BytesIO

import pytest
from fastapi import UploadFile

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import TryOnJobStatus, TryOnUploadRole
from src.use_cases.try_on.workflow_service import TryOnUploadValidationConfig, TryOnWorkflowService


def _upload(filename: str, content_type: str, payload: bytes) -> UploadFile:
    """Build an UploadFile suitable for direct use-case tests."""
    return UploadFile(file=BytesIO(payload), filename=filename, headers={"content-type": content_type})


@pytest.mark.asyncio
async def test_create_job_persists_validated_uploads_before_saving_job() -> None:
    """Try-On jobs must retain backend storage references for both uploaded inputs."""
    repository = InMemoryTryOnJobRepository()
    storage = InMemoryTryOnFileStorage()
    service = TryOnWorkflowService(
        repository=repository,
        generator=FakeTryOnGenerationAdapter(),
        file_storage=storage,
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={"image/jpeg"},
            max_upload_bytes=1024,
        ),
    )

    job = await service.create_job(
        human_photo=_upload("human.jpg", "image/jpeg", b"human-photo"),
        garment_photo=_upload("garment.jpg", "image/jpeg", b"garment-photo"),
    )

    assert job.status == TryOnJobStatus.COMPLETED
    assert [stored.role for stored in job.stored_inputs] == [
        TryOnUploadRole.HUMAN_PHOTO,
        TryOnUploadRole.GARMENT_PHOTO,
    ]
    assert all(stored.storage_backend == "in_memory" for stored in job.stored_inputs)
    assert all(stored.uri.startswith("memory://try-on/") for stored in job.stored_inputs)
    assert await repository.get(job.job_id) == job
```

Run and confirm failure:

```powershell
pytest tests/test_try_on_file_storage_workflow.py -q
```

Expected initial result: fails because `InMemoryTryOnFileStorage` and `file_storage` do not exist.

### Task 6: Implement in-memory file storage and wire the use case

Create `src/adapters/try_on/in_memory_file_storage.py`:

```python
"""In-memory Try-On file storage adapter for local development and tests."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.ports import TryOnFileStoragePort


@dataclass(frozen=True)
class StoredUploadPayload:
    """In-memory payload retained for tests and local sandbox behavior."""

    content_type: str
    payload: bytes


class InMemoryTryOnFileStorage(TryOnFileStoragePort):
    """Process-local file storage adapter that never touches external services."""

    def __init__(self) -> None:
        """Create an empty in-memory upload store."""
        self._uploads: dict[str, StoredUploadPayload] = {}
        self._lock = asyncio.Lock()

    async def save_upload(
        self,
        *,
        job_id: str,
        role: TryOnUploadRole,
        filename: str,
        content_type: str,
        payload: bytes,
        sha256_hex: str,
    ) -> TryOnStoredInput:
        """Persist upload bytes in process memory and return a stable memory URI."""
        object_name = f"{job_id}/{role.value}/{filename}"
        uri = f"memory://try-on/{object_name}"
        async with self._lock:
            self._uploads[uri] = StoredUploadPayload(content_type=content_type, payload=payload)
        return TryOnStoredInput(
            role=role,
            storage_backend="in_memory",
            uri=uri,
            object_name=object_name,
            content_type=content_type,
            size_bytes=len(payload),
            sha256=sha256_hex,
        )

    async def get_payload(self, uri: str) -> StoredUploadPayload | None:
        """Return a stored payload for tests and local diagnostics."""
        async with self._lock:
            return self._uploads.get(uri)
```

Modify `src/use_cases/try_on/workflow_service.py`:

- Import `TryOnFileStoragePort` and `TryOnStoredInput`.
- Add `file_storage: TryOnFileStoragePort` to the constructor.
- Store `self._file_storage = file_storage`.
- Replace `_extract_metadata` with a helper that returns both metadata and payload:

```python
@dataclass(frozen=True)
class ValidatedTryOnUpload:
    """Validated upload bytes and sanitized metadata for one Try-On input."""

    metadata: TryOnInputMetadata
    payload: bytes
```

Use this flow inside `create_job`:

```python
validated_uploads = [
    await self._validate_upload(TryOnUploadRole.HUMAN_PHOTO, human_photo),
    await self._validate_upload(TryOnUploadRole.GARMENT_PHOTO, garment_photo),
]
input_metadata = [validated.metadata for validated in validated_uploads]
job_id = f"try_on_{uuid4().hex}"
stored_inputs = [
    await self._file_storage.save_upload(
        job_id=job_id,
        role=validated.metadata.role,
        filename=validated.metadata.filename,
        content_type=validated.metadata.content_type,
        payload=validated.payload,
        sha256_hex=validated.metadata.sha256,
    )
    for validated in validated_uploads
]
```

Rename `_extract_metadata` to `_validate_upload` and return `ValidatedTryOnUpload`.

Add `stored_inputs: list[TryOnStoredInput]` parameter to `_build_job` and pass it into `TryOnJob(stored_inputs=stored_inputs, ...)`.

Run:

```powershell
pytest tests/test_try_on_file_storage_workflow.py tests/test_try_on_sandbox_lifecycle.py -q
```

Expected result: pass.

### Task 7: Add fake-backed GCS adapter tests

Create `tests/test_try_on_gcs_file_storage.py`.

Use local fake bucket/blob classes so no live GCS client is constructed:

```python
"""Tests for the Try-On GCS file storage adapter using local fakes."""
from __future__ import annotations

from src.adapters.try_on.gcs_file_storage import GcsTryOnFileStorage
from src.domain.try_on import TryOnUploadRole


class FakeBlob:
    """Minimal fake Cloud Storage blob."""

    def __init__(self, name: str) -> None:
        """Create a fake blob with no uploaded payload."""
        self.name = name
        self.uploaded_payload: bytes | None = None
        self.uploaded_content_type: str | None = None

    def upload_from_string(self, data: bytes, content_type: str) -> None:
        """Capture the uploaded bytes and content type."""
        self.uploaded_payload = data
        self.uploaded_content_type = content_type


class FakeBucket:
    """Minimal fake Cloud Storage bucket."""

    def __init__(self, name: str) -> None:
        """Create a fake bucket."""
        self.name = name
        self.blobs: dict[str, FakeBlob] = {}

    def blob(self, name: str) -> FakeBlob:
        """Return a fake blob by object name."""
        blob = FakeBlob(name)
        self.blobs[name] = blob
        return blob


async def test_gcs_file_storage_builds_prefixed_object_reference() -> None:
    """GCS adapter must upload bytes and return a non-public gs:// reference."""
    bucket = FakeBucket("fitfabrica-test-bucket")
    storage = GcsTryOnFileStorage(bucket=bucket, upload_prefix="try-on/uploads")

    stored = await storage.save_upload(
        job_id="try_on_123",
        role=TryOnUploadRole.HUMAN_PHOTO,
        filename="human photo.jpg",
        content_type="image/jpeg",
        payload=b"image-bytes",
        sha256_hex="a" * 64,
    )

    assert stored.storage_backend == "gcs"
    assert stored.bucket_name == "fitfabrica-test-bucket"
    assert stored.object_name == "try-on/uploads/try_on_123/human_photo/human-photo.jpg"
    assert stored.uri == "gs://fitfabrica-test-bucket/try-on/uploads/try_on_123/human_photo/human-photo.jpg"
    assert bucket.blobs[stored.object_name].uploaded_payload == b"image-bytes"
    assert bucket.blobs[stored.object_name].uploaded_content_type == "image/jpeg"
```

Run and confirm failure:

```powershell
pytest tests/test_try_on_gcs_file_storage.py -q
```

Expected initial result: fails because `GcsTryOnFileStorage` does not exist.

### Task 8: Implement GCS file storage adapter

Add `google-cloud-storage==3.6.0` to `requirements.txt`.

Create `src/adapters/try_on/gcs_file_storage.py`:

```python
"""Google Cloud Storage adapter for Try-On upload persistence."""
from __future__ import annotations

import re
from typing import Protocol

from google.cloud import storage

from src.domain.try_on import TryOnStoredInput, TryOnUploadRole
from src.use_cases.try_on.ports import TryOnFileStoragePort


class GcsBlob(Protocol):
    """Subset of a Cloud Storage blob used by this adapter."""

    name: str

    def upload_from_string(self, data: bytes, content_type: str) -> None:
        """Upload bytes to the object."""
        ...


class GcsBucket(Protocol):
    """Subset of a Cloud Storage bucket used by this adapter."""

    name: str

    def blob(self, name: str) -> GcsBlob:
        """Return a blob handle for an object name."""
        ...


class GcsTryOnFileStorage(TryOnFileStoragePort):
    """Persist Try-On uploads in Google Cloud Storage."""

    def __init__(self, bucket: GcsBucket, upload_prefix: str) -> None:
        """Create a GCS-backed upload storage adapter."""
        self._bucket = bucket
        self._upload_prefix = upload_prefix.strip("/")

    @classmethod
    def from_bucket_name(cls, bucket_name: str, upload_prefix: str) -> GcsTryOnFileStorage:
        """Create the adapter from a configured bucket name."""
        client = storage.Client()
        return cls(bucket=client.bucket(bucket_name), upload_prefix=upload_prefix)

    async def save_upload(
        self,
        *,
        job_id: str,
        role: TryOnUploadRole,
        filename: str,
        content_type: str,
        payload: bytes,
        sha256_hex: str,
    ) -> TryOnStoredInput:
        """Upload bytes to GCS and return an internal gs:// reference."""
        object_name = self._object_name(job_id=job_id, role=role, filename=filename)
        blob = self._bucket.blob(object_name)
        blob.upload_from_string(payload, content_type=content_type)
        return TryOnStoredInput(
            role=role,
            storage_backend="gcs",
            uri=f"gs://{self._bucket.name}/{object_name}",
            bucket_name=self._bucket.name,
            object_name=object_name,
            content_type=content_type,
            size_bytes=len(payload),
            sha256=sha256_hex,
        )

    def _object_name(self, *, job_id: str, role: TryOnUploadRole, filename: str) -> str:
        """Build a stable object path without exposing raw unsafe filename characters."""
        safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", filename).strip("-") or role.value
        return f"{self._upload_prefix}/{job_id}/{role.value}/{safe_filename}"
```

Run:

```powershell
pytest tests/test_try_on_gcs_file_storage.py -q
```

Expected result: pass.

### Task 9: Add fake-backed Firestore repository tests

Create `tests/test_try_on_firestore_repository.py`.

```python
"""Tests for Firestore Try-On repository serialization using local fakes."""
from __future__ import annotations

from src.adapters.try_on.firestore_repository import FirestoreTryOnJobRepository
from src.domain.try_on import TryOnJob, TryOnJobStatus, TryOnStoredInput, TryOnUploadRole


class FakeSnapshot:
    """Minimal Firestore document snapshot fake."""

    def __init__(self, exists: bool, data: dict[str, object] | None) -> None:
        """Create a fake snapshot."""
        self.exists = exists
        self._data = data

    def to_dict(self) -> dict[str, object] | None:
        """Return fake document data."""
        return self._data


class FakeDocument:
    """Minimal Firestore document fake."""

    def __init__(self) -> None:
        """Create an empty fake document."""
        self.data: dict[str, object] | None = None

    def set(self, data: dict[str, object]) -> None:
        """Persist fake document data."""
        self.data = data

    def get(self) -> FakeSnapshot:
        """Return a fake snapshot for the current document."""
        return FakeSnapshot(exists=self.data is not None, data=self.data)


class FakeCollection:
    """Minimal Firestore collection fake."""

    def __init__(self) -> None:
        """Create an empty fake collection."""
        self.documents: dict[str, FakeDocument] = {}

    def document(self, document_id: str) -> FakeDocument:
        """Return a fake document by ID."""
        if document_id not in self.documents:
            self.documents[document_id] = FakeDocument()
        return self.documents[document_id]


async def test_firestore_repository_round_trips_try_on_job() -> None:
    """Firestore repository must serialize and parse strict Try-On job models."""
    collection = FakeCollection()
    repository = FirestoreTryOnJobRepository(collection=collection)
    job = TryOnJob(
        job_id="try_on_123",
        status=TryOnJobStatus.GENERATING,
        stored_inputs=[
            TryOnStoredInput(
                role=TryOnUploadRole.HUMAN_PHOTO,
                storage_backend="gcs",
                uri="gs://bucket/key",
                bucket_name="bucket",
                object_name="key",
                content_type="image/jpeg",
                size_bytes=12,
                sha256="b" * 64,
            )
        ],
    )

    await repository.save(job)
    loaded = await repository.get("try_on_123")

    assert loaded == job


async def test_firestore_repository_returns_none_for_missing_job() -> None:
    """Missing Firestore documents must map to None."""
    repository = FirestoreTryOnJobRepository(collection=FakeCollection())

    assert await repository.get("missing") is None
```

Run and confirm failure:

```powershell
pytest tests/test_try_on_firestore_repository.py -q
```

Expected initial result: fails because `FirestoreTryOnJobRepository` does not exist.

### Task 10: Implement Firestore job repository adapter

Create `src/adapters/try_on/firestore_repository.py`:

```python
"""Firestore repository adapter for Try-On jobs."""
from __future__ import annotations

from typing import Protocol

from google.cloud import firestore

from src.domain.try_on import TryOnJob
from src.use_cases.try_on.ports import TryOnJobRepositoryPort


class FirestoreSnapshot(Protocol):
    """Subset of Firestore document snapshot used by this adapter."""

    exists: bool

    def to_dict(self) -> dict[str, object] | None:
        """Return document data."""
        ...


class FirestoreDocument(Protocol):
    """Subset of Firestore document reference used by this adapter."""

    def set(self, data: dict[str, object]) -> None:
        """Write document data."""
        ...

    def get(self) -> FirestoreSnapshot:
        """Read document data."""
        ...


class FirestoreCollection(Protocol):
    """Subset of Firestore collection reference used by this adapter."""

    def document(self, document_id: str) -> FirestoreDocument:
        """Return a document reference."""
        ...


class FirestoreTryOnJobRepository(TryOnJobRepositoryPort):
    """Persist Try-On jobs as strict JSON-compatible Firestore documents."""

    def __init__(self, collection: FirestoreCollection) -> None:
        """Create a Firestore repository from a collection reference."""
        self._collection = collection

    @classmethod
    def from_collection_name(cls, collection_name: str) -> FirestoreTryOnJobRepository:
        """Create the repository from a configured collection name."""
        client = firestore.Client()
        return cls(collection=client.collection(collection_name))

    async def save(self, job: TryOnJob) -> None:
        """Save a Try-On job document."""
        self._collection.document(job.job_id).set(job.model_dump(mode="json"))

    async def get(self, job_id: str) -> TryOnJob | None:
        """Return a Try-On job by ID, or None when it does not exist."""
        snapshot = self._collection.document(job_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict()
        if data is None:
            return None
        return TryOnJob.model_validate(data)
```

Run:

```powershell
pytest tests/test_try_on_firestore_repository.py -q
```

Expected result: pass.

### Task 11: Add route wiring tests

Create `tests/test_try_on_route_storage_wiring.py`.

Test only adapter selection. Do not create real Google clients.

```python
"""Route wiring tests for Try-On storage adapter selection."""
from __future__ import annotations

from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.entrypoints import try_on_routes
from src.settings import Settings


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "gcp_project_id": "test-project",
        "pubsub_topic_agent_jobs": "agent-jobs",
    }
    values.update(overrides)
    return Settings(**values)


def test_default_try_on_service_uses_in_memory_storage() -> None:
    """Default route wiring must stay local and non-durable."""
    service = try_on_routes._service(_settings())

    assert isinstance(service._repository, InMemoryTryOnJobRepository)
    assert isinstance(service._file_storage, InMemoryTryOnFileStorage)
```

Run and confirm failure if `_service` has not been updated:

```powershell
pytest tests/test_try_on_route_storage_wiring.py -q
```

Expected initial result: fails because `_service` does not pass file storage.

### Task 12: Wire adapter factories in routes

Modify `src/entrypoints/try_on_routes.py`.

Imports:

```python
from src.adapters.try_on.firestore_repository import FirestoreTryOnJobRepository
from src.adapters.try_on.gcs_file_storage import GcsTryOnFileStorage
from src.adapters.try_on.in_memory_file_storage import InMemoryTryOnFileStorage
from src.use_cases.try_on.ports import TryOnFileStoragePort, TryOnJobRepositoryPort
```

Replace `_repository()` with separate cached factories:

```python
@lru_cache(maxsize=1)
def _in_memory_repository() -> InMemoryTryOnJobRepository:
    """Return the process-local non-durable Try-On job repository."""
    return InMemoryTryOnJobRepository()


@lru_cache(maxsize=1)
def _in_memory_file_storage() -> InMemoryTryOnFileStorage:
    """Return the process-local non-durable Try-On file storage."""
    return InMemoryTryOnFileStorage()
```

Add:

```python
def _repository(settings: Settings) -> TryOnJobRepositoryPort:
    """Select the Try-On job repository adapter from settings."""
    if settings.try_on_job_repository_backend == "firestore":
        return FirestoreTryOnJobRepository.from_collection_name(settings.try_on_firestore_collection)
    return _in_memory_repository()


def _file_storage(settings: Settings) -> TryOnFileStoragePort:
    """Select the Try-On file storage adapter from settings."""
    if settings.try_on_file_storage_backend == "gcs":
        if settings.try_on_gcs_bucket_name is None:
            raise RuntimeError("try_on_gcs_bucket_name is required for GCS Try-On storage")
        return GcsTryOnFileStorage.from_bucket_name(
            bucket_name=settings.try_on_gcs_bucket_name,
            upload_prefix=settings.try_on_gcs_upload_prefix,
        )
    return _in_memory_file_storage()
```

Update `_service`:

```python
return TryOnWorkflowService(
    repository=_repository(settings),
    generator=FakeTryOnGenerationAdapter(),
    file_storage=_file_storage(settings),
    validation_config=TryOnUploadValidationConfig(
        allowed_content_types=set(settings.try_on_allowed_content_types),
        max_upload_bytes=settings.try_on_max_upload_bytes,
    ),
)
```

Run:

```powershell
pytest tests/test_try_on_route_storage_wiring.py tests/test_try_on_sandbox_lifecycle.py -q
```

Expected result: pass.

### Task 13: Update docs

Modify `docs/try-on-sandbox-api.md`.

Add a short backend storage note:

```markdown
## Storage Backend

The sandbox API remains stable while storage is selected server-side.

- Default local/test mode uses in-memory job and file storage.
- `try_on_file_storage_backend=gcs` enables GCS upload persistence only when `try_on_gcs_bucket_name` is configured.
- `try_on_job_repository_backend=firestore` enables Firestore job persistence only when `try_on_firestore_collection` is configured.
- Stored upload references are internal backend state and are not exposed as public result URLs.
- The sandbox still uses the fake generation adapter; this storage foundation does not call Vertex or production image generation.
```

Run the existing docs guard:

```powershell
pytest tests/test_try_on_sandbox_api_docs.py -q
```

Expected result: pass.

### Task 14: Full verification

Run focused backend checks:

```powershell
pytest tests/test_try_on_storage_settings.py tests/test_try_on_file_storage_workflow.py tests/test_try_on_gcs_file_storage.py tests/test_try_on_firestore_repository.py tests/test_try_on_route_storage_wiring.py tests/test_try_on_sandbox_lifecycle.py tests/test_try_on_sandbox_api_docs.py -q
```

Expected result: all pass.

Run architecture checks:

```powershell
pytest tests/architecture/test_http_routes_no_main_dependency.py tests/architecture/test_runtime_agents_no_side_effects.py -q
```

Expected result: all pass.

Run repository diff check:

```powershell
git diff --check
```

Expected result: no output.

### Task 15: Commit

Inspect changes:

```powershell
git status --short
git diff --stat
```

Commit:

```powershell
git add requirements.txt src/domain/try_on.py src/settings.py src/use_cases/try_on/ports.py src/use_cases/try_on/workflow_service.py src/entrypoints/try_on_routes.py src/adapters/try_on/in_memory_file_storage.py src/adapters/try_on/gcs_file_storage.py src/adapters/try_on/firestore_repository.py tests/test_try_on_file_storage_workflow.py tests/test_try_on_firestore_repository.py tests/test_try_on_gcs_file_storage.py tests/test_try_on_storage_settings.py tests/test_try_on_route_storage_wiring.py docs/try-on-sandbox-api.md
git commit -m "feat: add try-on durable storage foundation"
```

Expected result: one focused implementation commit.

## Acceptance Criteria

- Existing Try-On sandbox API tests still pass.
- New storage settings default to in-memory adapters.
- GCS and Firestore adapters are never constructed unless settings explicitly select them.
- GCS adapter tests use fake bucket/blob classes and do not make network calls.
- Firestore adapter tests use fake collection/document/snapshot classes and do not make network calls.
- Stored upload references are persisted on `TryOnJob` as backend-owned internal state.
- Public API responses do not expose raw storage object details.
- No Vertex, GCS, or Firestore live resource is called during local verification.
- Documentation explains the storage backend boundary.
