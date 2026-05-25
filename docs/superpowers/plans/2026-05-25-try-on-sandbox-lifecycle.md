# Try-On Sandbox Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real `apps/web` to backend Try-On sandbox lifecycle with multipart upload, typed jobs, status polling, deterministic fake generation, result display, and sandbox cost events.

**Architecture:** Backend owns all workflow state through FastAPI endpoints and a use-case/service layer. The first repository is in-memory and non-durable, while fake generation sits behind a replaceable port so GCS and real AI can be added without changing the frontend contract.

**Tech Stack:** FastAPI, Pydantic, pytest, Next.js, React, TypeScript.

---

## File Structure

- Create `src/domain/try_on.py`: Pydantic/domain models, enums, typed errors, validation settings.
- Create `src/use_cases/try_on/__init__.py`: package exports.
- Create `src/use_cases/try_on/ports.py`: repository and generation ports.
- Create `src/use_cases/try_on/workflow_service.py`: validation, job lifecycle, status history, result creation.
- Create `src/adapters/try_on/__init__.py`: adapter package.
- Create `src/adapters/try_on/in_memory_repository.py`: first non-durable job repository.
- Create `src/adapters/try_on/fake_generation.py`: deterministic fake generation adapter.
- Create `src/entrypoints/try_on_routes.py`: `POST /api/try-on/jobs`, `GET /api/jobs/{job_id}/status`, `GET /api/jobs/{job_id}/result`.
- Modify `src/entrypoints/http_routes.py`: include Try-On router.
- Modify `src/settings.py`: add file validation configuration.
- Create `tests/test_try_on_sandbox_lifecycle.py`: backend lifecycle and validation tests.
- Modify `apps/web/src/lib/api/contracts.ts`: typed Try-On request/response contracts.
- Modify `apps/web/src/lib/api/client.ts`: typed Try-On API methods.
- Create `apps/web/src/features/workspace/try-on-workflow.tsx`: client workflow for `/workspace/try-on/new`.
- Modify `apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx`: render the client workflow.
- Create `apps/web/src/features/workspace/try-on-result.tsx`: client result loader and renderer.
- Modify `apps/web/src/app/(workspace)/workspace/try-on/result/page.tsx`: render result component.

---

### Task 1: Backend Domain Models And Settings

**Files:**
- Create: `src/domain/try_on.py`
- Modify: `src/settings.py`
- Test: `tests/test_try_on_sandbox_lifecycle.py`

- [ ] **Step 1: Write failing domain/settings tests**

Add the first tests to `tests/test_try_on_sandbox_lifecycle.py`:

```python
from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_try_on_missing_files_returns_typed_error():
    response = client.post("/api/try-on/jobs", files={})

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "missing_required_file"
    assert body["error"]["details"]["fields"] == ["human_photo", "garment_photo"]


def test_try_on_rejects_unsupported_content_type():
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.txt", b"hello", "text/plain"),
            "garment_photo": ("garment.png", b"fake-image", "image/png"),
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "unsupported_content_type"
    assert body["error"]["details"]["field"] == "human_photo"
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
pytest tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: failure because `/api/try-on/jobs` does not exist yet.

- [ ] **Step 3: Add Try-On domain models**

Create `src/domain/try_on.py`:

```python
"""Domain contracts for the FitFabrica Try-On workflow."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class TryOnWorkflowType(StrEnum):
    """Supported workflow type for the first FitFabrica cycle."""

    TRY_ON = "try_on"


class TryOnJobStatus(StrEnum):
    """Explicit Try-On lifecycle statuses exposed to clients."""

    ACCEPTED = "accepted"
    VALIDATING_INPUTS = "validating_inputs"
    GENERATING = "generating"
    QUALITY_CHECKING = "quality_checking"
    COMPLETED = "completed"
    FAILED = "failed"


class TryOnUploadRole(StrEnum):
    """Input image roles required by the Try-On workflow."""

    HUMAN_PHOTO = "human_photo"
    GARMENT_PHOTO = "garment_photo"


class TryOnChargeStatus(StrEnum):
    """Credit charge status for sandbox cost events."""

    NOT_CHARGED = "not_charged"


class TryOnErrorCode(StrEnum):
    """Typed Try-On API error codes."""

    MISSING_REQUIRED_FILE = "missing_required_file"
    UNSUPPORTED_CONTENT_TYPE = "unsupported_content_type"
    EMPTY_FILE = "empty_file"
    FILE_TOO_LARGE = "file_too_large"
    JOB_NOT_FOUND = "job_not_found"
    RESULT_NOT_READY = "result_not_ready"
    JOB_FAILED = "job_failed"


class TryOnInputMetadata(BaseModel):
    """Sandbox-safe metadata extracted from an uploaded image."""

    role: TryOnUploadRole
    filename: str
    content_type: str
    size_bytes: int = Field(ge=0)
    sha256: str


class TryOnStatusEvent(BaseModel):
    """A status transition recorded by backend orchestration."""

    status: TryOnJobStatus
    stage: str
    message: str
    occurred_at: datetime


class TryOnCostEvent(BaseModel):
    """Sandbox cost event. No real credits are deducted in this cycle."""

    event_type: str
    estimated_units: int = Field(ge=0)
    charge_status: TryOnChargeStatus
    charged_credits: int = Field(ge=0)
    occurred_at: datetime


class TryOnQualityCheck(BaseModel):
    """One quality verifier style check result."""

    name: str
    status: Literal["passed", "warning", "failed"]
    confidence: float = Field(ge=0.0, le=1.0)
    message: str


class TryOnQualityReport(BaseModel):
    """Quality report shaped like the future Quality Verifier Agent output."""

    verdict: Literal["pass", "repair_recommended", "reject"]
    confidence: float = Field(ge=0.0, le=1.0)
    checks: list[TryOnQualityCheck]
    limitations: list[str]


class TryOnResultImage(BaseModel):
    """Reference to the generated result image."""

    kind: Literal["sandbox_placeholder"]
    url: str
    alt: str


class TryOnResult(BaseModel):
    """Completed Try-On result returned to the web app."""

    job_id: str
    workflow_type: TryOnWorkflowType
    result_image: TryOnResultImage
    quality_report: TryOnQualityReport
    stylist_note: str
    input_metadata: list[TryOnInputMetadata]
    completed_at: datetime


class TryOnError(BaseModel):
    """Typed error payload returned by Try-On endpoints."""

    code: TryOnErrorCode
    message: str
    details: dict[str, object]


class TryOnJob(BaseModel):
    """Backend-owned Try-On job state."""

    job_id: str
    workflow_type: TryOnWorkflowType
    status: TryOnJobStatus
    created_at: datetime
    updated_at: datetime
    input_metadata: list[TryOnInputMetadata]
    status_history: list[TryOnStatusEvent]
    cost_events: list[TryOnCostEvent]
    result: TryOnResult | None = None
    error: TryOnError | None = None


class TryOnJobCreatedResponse(BaseModel):
    """Response returned after a Try-On job is accepted."""

    job_id: str
    workflow_type: TryOnWorkflowType
    status: TryOnJobStatus
    input_metadata: list[TryOnInputMetadata]
    status_url: str
    result_url: str


class TryOnJobStatusResponse(BaseModel):
    """Current status and full status history."""

    job_id: str
    workflow_type: TryOnWorkflowType
    status: TryOnJobStatus
    status_history: list[TryOnStatusEvent]
    cost_events: list[TryOnCostEvent]


class TryOnResultResponse(BaseModel):
    """Result endpoint response for a completed job."""

    status: Literal["completed"]
    job_id: str
    workflow_type: TryOnWorkflowType
    result: TryOnResult


class TryOnNotReadyResponse(BaseModel):
    """Result endpoint response for an existing but unfinished job."""

    status: Literal["not_ready"]
    job_id: str
    workflow_type: TryOnWorkflowType
    current_status: TryOnJobStatus
    status_url: str


class TryOnErrorResponse(BaseModel):
    """Envelope for typed Try-On errors."""

    error: TryOnError


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamps for job records."""

    return datetime.now(timezone.utc)
```

- [ ] **Step 4: Add configuration-driven upload validation settings**

Modify `src/settings.py` inside `class Settings`:

```python
    try_on_allowed_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["image/jpeg", "image/png", "image/webp"],
        validation_alias=AliasChoices("TRY_ON_ALLOWED_CONTENT_TYPES"),
    )
    try_on_max_upload_bytes: int = Field(
        default=10 * 1024 * 1024,
        validation_alias=AliasChoices("TRY_ON_MAX_UPLOAD_BYTES"),
    )
```

Add a validator near the existing list validators:

```python
    @field_validator("try_on_allowed_content_types", mode="before")
    @classmethod
    def _parse_try_on_content_types(cls, value):
        if value in (None, "", []):
            return ["image/jpeg", "image/png", "image/webp"]
        if isinstance(value, str):
            return [part.strip().lower() for part in value.split(",") if part.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip().lower() for item in value if str(item).strip()]
        return [str(value).strip().lower()]
```

- [ ] **Step 5: Run focused tests**

Run:

```powershell
pytest tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: still fails because routes are not implemented, but settings/model imports are valid.

- [ ] **Step 6: Commit Task 1**

Run:

```powershell
git add src/domain/try_on.py src/settings.py tests/test_try_on_sandbox_lifecycle.py
git commit -m "feat: add try-on sandbox domain contracts"
```

---

### Task 2: Repository, Generation Port, And Workflow Service

**Files:**
- Create: `src/use_cases/try_on/__init__.py`
- Create: `src/use_cases/try_on/ports.py`
- Create: `src/use_cases/try_on/workflow_service.py`
- Create: `src/adapters/try_on/__init__.py`
- Create: `src/adapters/try_on/in_memory_repository.py`
- Create: `src/adapters/try_on/fake_generation.py`
- Test: `tests/test_try_on_sandbox_lifecycle.py`

- [ ] **Step 1: Add workflow lifecycle tests**

Append to `tests/test_try_on_sandbox_lifecycle.py`:

```python
def test_try_on_job_creation_records_status_history_and_cost_events():
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.png", b"human-image-bytes", "image/png"),
            "garment_photo": ("garment.webp", b"garment-image-bytes", "image/webp"),
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["workflow_type"] == "try_on"
    assert created["status"] == "completed"
    assert created["status_url"] == f"/api/jobs/{created['job_id']}/status"
    assert created["result_url"] == f"/api/jobs/{created['job_id']}/result"

    status_response = client.get(created["status_url"])
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert [event["status"] for event in status_body["status_history"]] == [
        "accepted",
        "validating_inputs",
        "generating",
        "quality_checking",
        "completed",
    ]
    assert status_body["cost_events"][0]["charge_status"] == "not_charged"
    assert status_body["cost_events"][0]["charged_credits"] == 0


def test_try_on_result_contract_is_structurally_realistic():
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.jpg", b"human-image-bytes", "image/jpeg"),
            "garment_photo": ("garment.png", b"garment-image-bytes", "image/png"),
        },
    )
    job_id = response.json()["job_id"]

    result_response = client.get(f"/api/jobs/{job_id}/result")

    assert result_response.status_code == 200
    body = result_response.json()
    assert body["status"] == "completed"
    assert body["result"]["workflow_type"] == "try_on"
    assert body["result"]["result_image"]["kind"] == "sandbox_placeholder"
    assert body["result"]["quality_report"]["verdict"] == "pass"
    assert body["result"]["quality_report"]["checks"][0]["name"] == "face_preservation"
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
pytest tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: failure because service, repository, generator, and routes are not wired.

- [ ] **Step 3: Add repository and generator ports**

Create `src/use_cases/try_on/ports.py`:

```python
"""Ports for the Try-On workflow use case."""
from __future__ import annotations

from typing import Protocol

from src.domain.try_on import TryOnInputMetadata, TryOnJob, TryOnResult


class TryOnJobRepositoryPort(Protocol):
    """Persistence boundary for Try-On jobs."""

    async def save(self, job: TryOnJob) -> None:
        """Persist the provided job state."""

    async def get(self, job_id: str) -> TryOnJob | None:
        """Return a job by id when it exists."""


class TryOnGenerationPort(Protocol):
    """Generation boundary for fake and future real Try-On adapters."""

    async def generate(self, *, job_id: str, input_metadata: list[TryOnInputMetadata]) -> TryOnResult:
        """Generate a Try-On result from validated input metadata."""
```

Create `src/use_cases/try_on/__init__.py`:

```python
"""Try-On workflow use cases."""
```

- [ ] **Step 4: Add in-memory repository**

Create `src/adapters/try_on/in_memory_repository.py`:

```python
"""Non-durable in-memory repository for the first Try-On sandbox proof."""
from __future__ import annotations

import asyncio

from src.domain.try_on import TryOnJob
from src.use_cases.try_on.ports import TryOnJobRepositoryPort


class InMemoryTryOnJobRepository(TryOnJobRepositoryPort):
    """Store jobs in process memory. Jobs disappear after backend restart."""

    def __init__(self) -> None:
        self._jobs: dict[str, TryOnJob] = {}
        self._lock = asyncio.Lock()

    async def save(self, job: TryOnJob) -> None:
        """Persist a job snapshot in memory."""
        async with self._lock:
            self._jobs[job.job_id] = job

    async def get(self, job_id: str) -> TryOnJob | None:
        """Return a job snapshot from memory."""
        async with self._lock:
            return self._jobs.get(job_id)
```

Create `src/adapters/try_on/__init__.py`:

```python
"""Try-On adapters."""
```

- [ ] **Step 5: Add deterministic fake generation adapter**

Create `src/adapters/try_on/fake_generation.py`:

```python
"""Deterministic fake Try-On generation adapter."""
from __future__ import annotations

from src.domain.try_on import (
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnWorkflowType,
    utc_now,
)
from src.use_cases.try_on.ports import TryOnGenerationPort


class FakeTryOnGenerationAdapter(TryOnGenerationPort):
    """Return a stable result shaped like the future real generation output."""

    async def generate(self, *, job_id: str, input_metadata: list[TryOnInputMetadata]) -> TryOnResult:
        """Generate deterministic sandbox output for a validated job."""
        return TryOnResult(
            job_id=job_id,
            workflow_type=TryOnWorkflowType.TRY_ON,
            result_image=TryOnResultImage(
                kind="sandbox_placeholder",
                url="/images/shared/try-on-sandbox-result.webp",
                alt="Sandbox Try-On result preview",
            ),
            quality_report=TryOnQualityReport(
                verdict="pass",
                confidence=0.91,
                checks=[
                    TryOnQualityCheck(
                        name="face_preservation",
                        status="passed",
                        confidence=0.92,
                        message="Sandbox verifier confirms the face-preservation check shape.",
                    ),
                    TryOnQualityCheck(
                        name="garment_similarity",
                        status="passed",
                        confidence=0.9,
                        message="Sandbox verifier confirms garment-similarity reporting shape.",
                    ),
                    TryOnQualityCheck(
                        name="artifact_scan",
                        status="warning",
                        confidence=0.74,
                        message="Sandbox output is deterministic and not a real image generation.",
                    ),
                ],
                limitations=["Sandbox fake generation does not evaluate the uploaded pixels."],
            ),
            stylist_note="Sandbox Try-On completed. Real stylist advice will be generated after the production generation adapter is connected.",
            input_metadata=input_metadata,
            completed_at=utc_now(),
        )
```

- [ ] **Step 6: Add workflow service**

Create `src/use_cases/try_on/workflow_service.py`:

```python
"""Try-On workflow orchestration service."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from uuid import uuid4

from starlette.datastructures import UploadFile

from src.domain.try_on import (
    TryOnChargeStatus,
    TryOnCostEvent,
    TryOnError,
    TryOnErrorCode,
    TryOnInputMetadata,
    TryOnJob,
    TryOnJobStatus,
    TryOnStatusEvent,
    TryOnUploadRole,
    TryOnWorkflowType,
    utc_now,
)
from src.use_cases.try_on.ports import TryOnGenerationPort, TryOnJobRepositoryPort


@dataclass(frozen=True)
class TryOnUploadValidationConfig:
    """Configuration for sandbox upload validation."""

    allowed_content_types: set[str]
    max_upload_bytes: int


class TryOnValidationError(Exception):
    """Raised when upload validation fails."""

    def __init__(self, error: TryOnError) -> None:
        super().__init__(error.message)
        self.error = error


class TryOnWorkflowService:
    """Create and execute Try-On jobs through backend-owned lifecycle rules."""

    def __init__(
        self,
        *,
        repository: TryOnJobRepositoryPort,
        generator: TryOnGenerationPort,
        validation_config: TryOnUploadValidationConfig,
    ) -> None:
        self.repository = repository
        self.generator = generator
        self.validation_config = validation_config

    async def create_job(self, *, human_photo: UploadFile | None, garment_photo: UploadFile | None) -> TryOnJob:
        """Validate uploaded files, run sandbox generation, and persist the job."""
        missing = []
        if human_photo is None:
            missing.append("human_photo")
        if garment_photo is None:
            missing.append("garment_photo")
        if missing:
            raise TryOnValidationError(
                TryOnError(
                    code=TryOnErrorCode.MISSING_REQUIRED_FILE,
                    message="Required Try-On upload files are missing.",
                    details={"fields": missing},
                )
            )

        now = utc_now()
        job = TryOnJob(
            job_id=f"tryon_{uuid4().hex}",
            workflow_type=TryOnWorkflowType.TRY_ON,
            status=TryOnJobStatus.ACCEPTED,
            created_at=now,
            updated_at=now,
            input_metadata=[],
            status_history=[],
            cost_events=[],
        )
        self._transition(job, TryOnJobStatus.ACCEPTED, "accepted", "Try-On job accepted by backend.")
        self._transition(job, TryOnJobStatus.VALIDATING_INPUTS, "input_validation", "Validating uploaded files.")

        job.input_metadata = [
            await self._metadata_for_upload(role=TryOnUploadRole.HUMAN_PHOTO, upload=human_photo),
            await self._metadata_for_upload(role=TryOnUploadRole.GARMENT_PHOTO, upload=garment_photo),
        ]

        self._transition(job, TryOnJobStatus.GENERATING, "sandbox_generation", "Running deterministic sandbox generation.")
        job.result = await self.generator.generate(job_id=job.job_id, input_metadata=job.input_metadata)

        self._transition(job, TryOnJobStatus.QUALITY_CHECKING, "quality_check", "Recording sandbox quality report.")
        job.cost_events.append(
            TryOnCostEvent(
                event_type="try_on_sandbox_generation",
                estimated_units=1,
                charge_status=TryOnChargeStatus.NOT_CHARGED,
                charged_credits=0,
                occurred_at=utc_now(),
            )
        )
        self._transition(job, TryOnJobStatus.COMPLETED, "completed", "Sandbox Try-On result is ready.")
        await self.repository.save(job)
        return job

    async def get_job(self, job_id: str) -> TryOnJob | None:
        """Return a Try-On job by id."""
        return await self.repository.get(job_id)

    async def _metadata_for_upload(self, *, role: TryOnUploadRole, upload: UploadFile) -> TryOnInputMetadata:
        content_type = (upload.content_type or "").lower()
        if content_type not in self.validation_config.allowed_content_types:
            raise TryOnValidationError(
                TryOnError(
                    code=TryOnErrorCode.UNSUPPORTED_CONTENT_TYPE,
                    message="Uploaded file content type is not supported.",
                    details={"field": role.value, "content_type": content_type},
                )
            )

        content = await upload.read()
        await upload.seek(0)
        size_bytes = len(content)
        if size_bytes == 0:
            raise TryOnValidationError(
                TryOnError(
                    code=TryOnErrorCode.EMPTY_FILE,
                    message="Uploaded file is empty.",
                    details={"field": role.value},
                )
            )
        if size_bytes > self.validation_config.max_upload_bytes:
            raise TryOnValidationError(
                TryOnError(
                    code=TryOnErrorCode.FILE_TOO_LARGE,
                    message="Uploaded file exceeds the configured maximum size.",
                    details={
                        "field": role.value,
                        "size_bytes": size_bytes,
                        "max_upload_bytes": self.validation_config.max_upload_bytes,
                    },
                )
            )

        return TryOnInputMetadata(
            role=role,
            filename=upload.filename or role.value,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def _transition(self, job: TryOnJob, status: TryOnJobStatus, stage: str, message: str) -> None:
        job.status = status
        job.updated_at = utc_now()
        job.status_history.append(
            TryOnStatusEvent(
                status=status,
                stage=stage,
                message=message,
                occurred_at=job.updated_at,
            )
        )
```

- [ ] **Step 7: Run focused tests**

Run:

```powershell
pytest tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: still fails until routes are added.

- [ ] **Step 8: Commit Task 2**

Run:

```powershell
git add src/use_cases/try_on src/adapters/try_on tests/test_try_on_sandbox_lifecycle.py
git commit -m "feat: add try-on sandbox workflow service"
```

---

### Task 3: FastAPI Try-On Routes

**Files:**
- Create: `src/entrypoints/try_on_routes.py`
- Modify: `src/entrypoints/http_routes.py`
- Test: `tests/test_try_on_sandbox_lifecycle.py`

- [ ] **Step 1: Add remaining route tests**

Append to `tests/test_try_on_sandbox_lifecycle.py`:

```python
def test_try_on_rejects_empty_file():
    response = client.post(
        "/api/try-on/jobs",
        files={
            "human_photo": ("human.png", b"", "image/png"),
            "garment_photo": ("garment.png", b"garment-image", "image/png"),
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_file"
    assert response.json()["error"]["details"]["field"] == "human_photo"


def test_try_on_unknown_status_job_returns_typed_error():
    response = client.get("/api/jobs/tryon_missing/status")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "job_not_found"


def test_try_on_unknown_result_job_returns_typed_error():
    response = client.get("/api/jobs/tryon_missing/result")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "job_not_found"
```

- [ ] **Step 2: Run tests and verify route failures**

Run:

```powershell
pytest tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: failures for missing route implementation.

- [ ] **Step 3: Add Try-On route module**

Create `src/entrypoints/try_on_routes.py`:

```python
"""FastAPI routes for the FitFabrica Try-On sandbox workflow."""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import JSONResponse

from src.adapters.try_on.fake_generation import FakeTryOnGenerationAdapter
from src.adapters.try_on.in_memory_repository import InMemoryTryOnJobRepository
from src.domain.try_on import (
    TryOnError,
    TryOnErrorCode,
    TryOnErrorResponse,
    TryOnJobCreatedResponse,
    TryOnJobStatus,
    TryOnJobStatusResponse,
    TryOnNotReadyResponse,
    TryOnResultResponse,
)
from src.settings import Settings
from src.use_cases.try_on.workflow_service import (
    TryOnUploadValidationConfig,
    TryOnValidationError,
    TryOnWorkflowService,
)

router = APIRouter()


@lru_cache(maxsize=1)
def _repository() -> InMemoryTryOnJobRepository:
    """Return the process-local non-durable sandbox repository."""
    return InMemoryTryOnJobRepository()


def _service(settings: Settings) -> TryOnWorkflowService:
    return TryOnWorkflowService(
        repository=_repository(),
        generator=FakeTryOnGenerationAdapter(),
        validation_config=TryOnUploadValidationConfig(
            allowed_content_types={item.lower() for item in settings.try_on_allowed_content_types},
            max_upload_bytes=settings.try_on_max_upload_bytes,
        ),
    )


def _error_response(status_code: int, error: TryOnError) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=TryOnErrorResponse(error=error).model_dump(mode="json"))


@router.post("/api/try-on/jobs")
async def create_try_on_job(
    request: Request,
    human_photo: UploadFile | None = File(default=None),
    garment_photo: UploadFile | None = File(default=None),
) -> JSONResponse:
    """Create and execute a sandbox Try-On job from multipart uploads."""
    try:
        job = await _service(request.app.state.settings).create_job(
            human_photo=human_photo,
            garment_photo=garment_photo,
        )
    except TryOnValidationError as exc:
        return _error_response(422, exc.error)

    body = TryOnJobCreatedResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        status=job.status,
        input_metadata=job.input_metadata,
        status_url=f"/api/jobs/{job.job_id}/status",
        result_url=f"/api/jobs/{job.job_id}/result",
    )
    return JSONResponse(status_code=201, content=body.model_dump(mode="json"))


@router.get("/api/jobs/{job_id}/status")
async def get_job_status(request: Request, job_id: str) -> JSONResponse:
    """Return current status and status history for a Try-On job."""
    job = await _service(request.app.state.settings).get_job(job_id)
    if job is None:
        return _error_response(
            404,
            TryOnError(
                code=TryOnErrorCode.JOB_NOT_FOUND,
                message="Try-On job was not found.",
                details={"job_id": job_id},
            ),
        )

    body = TryOnJobStatusResponse(
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        status=job.status,
        status_history=job.status_history,
        cost_events=job.cost_events,
    )
    return JSONResponse(status_code=200, content=body.model_dump(mode="json"))


@router.get("/api/jobs/{job_id}/result")
async def get_job_result(request: Request, job_id: str) -> JSONResponse:
    """Return a completed Try-On result or a typed not-ready response."""
    job = await _service(request.app.state.settings).get_job(job_id)
    if job is None:
        return _error_response(
            404,
            TryOnError(
                code=TryOnErrorCode.JOB_NOT_FOUND,
                message="Try-On job was not found.",
                details={"job_id": job_id},
            ),
        )

    if job.status == TryOnJobStatus.FAILED:
        return _error_response(
            409,
            job.error
            or TryOnError(
                code=TryOnErrorCode.JOB_FAILED,
                message="Try-On job failed.",
                details={"job_id": job_id},
            ),
        )

    if job.status != TryOnJobStatus.COMPLETED or job.result is None:
        body = TryOnNotReadyResponse(
            status="not_ready",
            job_id=job.job_id,
            workflow_type=job.workflow_type,
            current_status=job.status,
            status_url=f"/api/jobs/{job.job_id}/status",
        )
        return JSONResponse(status_code=202, content=body.model_dump(mode="json"))

    body = TryOnResultResponse(
        status="completed",
        job_id=job.job_id,
        workflow_type=job.workflow_type,
        result=job.result,
    )
    return JSONResponse(status_code=200, content=body.model_dump(mode="json"))
```

- [ ] **Step 4: Include router**

Modify `src/entrypoints/http_routes.py`:

```python
from .try_on_routes import router as try_on_router
```

Then include it:

```python
router.include_router(try_on_router)
```

- [ ] **Step 5: Run backend tests**

Run:

```powershell
pytest tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: all Try-On sandbox lifecycle tests pass.

- [ ] **Step 6: Run architecture route guardrail**

Run:

```powershell
pytest tests/architecture/test_http_routes_no_main_dependency.py -q
```

Expected: pass.

- [ ] **Step 7: Commit Task 3**

Run:

```powershell
git add src/entrypoints/try_on_routes.py src/entrypoints/http_routes.py tests/test_try_on_sandbox_lifecycle.py
git commit -m "feat: expose try-on sandbox job api"
```

---

### Task 4: Frontend API Contracts And Client

**Files:**
- Modify: `apps/web/src/lib/api/contracts.ts`
- Modify: `apps/web/src/lib/api/client.ts`

- [ ] **Step 1: Add typed Try-On contracts**

Append to `apps/web/src/lib/api/contracts.ts`:

```typescript
export type TryOnWorkflowType = "try_on";

export type TryOnJobStatus =
  | "accepted"
  | "validating_inputs"
  | "generating"
  | "quality_checking"
  | "completed"
  | "failed";

export type TryOnInputMetadata = {
  role: "human_photo" | "garment_photo";
  filename: string;
  content_type: string;
  size_bytes: number;
  sha256: string;
};

export type TryOnStatusEvent = {
  status: TryOnJobStatus;
  stage: string;
  message: string;
  occurred_at: string;
};

export type TryOnCostEvent = {
  event_type: string;
  estimated_units: number;
  charge_status: "not_charged";
  charged_credits: number;
  occurred_at: string;
};

export type TryOnQualityCheck = {
  name: string;
  status: "passed" | "warning" | "failed";
  confidence: number;
  message: string;
};

export type TryOnQualityReport = {
  verdict: "pass" | "repair_recommended" | "reject";
  confidence: number;
  checks: TryOnQualityCheck[];
  limitations: string[];
};

export type TryOnResult = {
  job_id: string;
  workflow_type: TryOnWorkflowType;
  result_image: {
    kind: "sandbox_placeholder";
    url: string;
    alt: string;
  };
  quality_report: TryOnQualityReport;
  stylist_note: string;
  input_metadata: TryOnInputMetadata[];
  completed_at: string;
};

export type TryOnJobCreatedResponse = {
  job_id: string;
  workflow_type: TryOnWorkflowType;
  status: TryOnJobStatus;
  input_metadata: TryOnInputMetadata[];
  status_url: string;
  result_url: string;
};

export type TryOnJobStatusResponse = {
  job_id: string;
  workflow_type: TryOnWorkflowType;
  status: TryOnJobStatus;
  status_history: TryOnStatusEvent[];
  cost_events: TryOnCostEvent[];
};

export type TryOnResultResponse =
  | {
      status: "completed";
      job_id: string;
      workflow_type: TryOnWorkflowType;
      result: TryOnResult;
    }
  | {
      status: "not_ready";
      job_id: string;
      workflow_type: TryOnWorkflowType;
      current_status: TryOnJobStatus;
      status_url: string;
    };

export type ApiErrorResponse = {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
};
```

- [ ] **Step 2: Add typed API client methods**

Modify `apps/web/src/lib/api/client.ts` imports:

```typescript
import type {
  DemoRequestDto,
  SignInDto,
  TryOnJobCreatedResponse,
  TryOnJobStatusResponse,
  TryOnResultResponse
} from "@/lib/api/contracts";
```

Add methods inside `WebApiClient`:

```typescript
  public async createTryOnJob(payload: FormData): Promise<TryOnJobCreatedResponse> {
    const response = await fetch(`${this.baseUrl}/api/try-on/jobs`, {
      method: "POST",
      body: payload
    });

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnJobCreatedResponse>;
  }

  public async getJobStatus(jobId: string): Promise<TryOnJobStatusResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/status`);

    if (!response.ok) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnJobStatusResponse>;
  }

  public async getJobResult(jobId: string): Promise<TryOnResultResponse> {
    const response = await fetch(`${this.baseUrl}/api/jobs/${jobId}/result`);

    if (!response.ok && response.status !== 202) {
      throw new Error(await this.errorMessage(response));
    }

    return response.json() as Promise<TryOnResultResponse>;
  }

  private async errorMessage(response: Response): Promise<string> {
    try {
      const body = (await response.json()) as { error?: { message?: string } };
      return body.error?.message ?? "Backend request failed.";
    } catch {
      return "Backend request failed.";
    }
  }
```

- [ ] **Step 3: Run frontend typecheck**

Run:

```powershell
npm --prefix apps/web run typecheck
```

Expected: pass.

- [ ] **Step 4: Commit Task 4**

Run:

```powershell
git add apps/web/src/lib/api/contracts.ts apps/web/src/lib/api/client.ts
git commit -m "feat: add try-on web api contracts"
```

---

### Task 5: New Try-On Page Integration

**Files:**
- Create: `apps/web/src/features/workspace/try-on-workflow.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx`

- [ ] **Step 1: Create client workflow component**

Create `apps/web/src/features/workspace/try-on-workflow.tsx`:

```typescript
"use client";

import { useRouter } from "next/navigation";
import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";
import type { TryOnJobStatusResponse } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";

const allowedTypes = new Set(["image/jpeg", "image/png", "image/webp"]);
const maxFileSizeBytes = 10 * 1024 * 1024;

type SelectedFile = {
  file: File;
  previewUrl: string;
};

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

function validateFile(file: File): string {
  if (!allowedTypes.has(file.type)) {
    return "Поддерживаются только JPEG, PNG и WEBP.";
  }
  if (file.size === 0) {
    return "Файл пустой. Выберите другое изображение.";
  }
  if (file.size > maxFileSizeBytes) {
    return "Файл больше 10MB. Выберите изображение меньшего размера.";
  }
  return "";
}

function UploadPanel({
  label,
  selected,
  onChange
}: {
  label: string;
  selected: SelectedFile | null;
  onChange: (file: File | null) => void;
}) {
  return (
    <label className="upload-card grid w-full gap-4 border-2 border-dashed border-[#d8c3a5] bg-[var(--surface)] p-4 text-center">
      <span className="upload-card-title font-semibold">{label}</span>
      {selected ? (
        <img alt={label} className="h-[220px] w-full rounded-[1.5rem] object-cover" src={selected.previewUrl} />
      ) : (
        <div className="flex h-[220px] items-center justify-center rounded-[1.5rem] bg-[var(--ai-soft)] text-[0.9rem] font-semibold text-[var(--text-secondary)]">
          JPEG, PNG, WEBP до 10MB
        </div>
      )}
      <input
        accept="image/jpeg,image/png,image/webp"
        className="sr-only"
        onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(event.target.files?.[0] ?? null)}
        type="file"
      />
      <span className="site-pill-button site-pill-button--compact justify-center">Выбрать файл</span>
    </label>
  );
}

export function TryOnWorkflow() {
  const router = useRouter();
  const [humanPhoto, setHumanPhoto] = useState<SelectedFile | null>(null);
  const [garmentPhoto, setGarmentPhoto] = useState<SelectedFile | null>(null);
  const [status, setStatus] = useState<TryOnJobStatusResponse | null>(null);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    return () => {
      if (humanPhoto) URL.revokeObjectURL(humanPhoto.previewUrl);
      if (garmentPhoto) URL.revokeObjectURL(garmentPhoto.previewUrl);
    };
  }, [humanPhoto, garmentPhoto]);

  function selectHumanPhoto(file: File | null) {
    if (humanPhoto) URL.revokeObjectURL(humanPhoto.previewUrl);
    setHumanPhoto(file ? { file, previewUrl: URL.createObjectURL(file) } : null);
  }

  function selectGarmentPhoto(file: File | null) {
    if (garmentPhoto) URL.revokeObjectURL(garmentPhoto.previewUrl);
    setGarmentPhoto(file ? { file, previewUrl: URL.createObjectURL(file) } : null);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setStatus(null);

    if (!humanPhoto || !garmentPhoto) {
      setError("Загрузите фото человека и фото одежды.");
      return;
    }

    const localError = validateFile(humanPhoto.file) || validateFile(garmentPhoto.file);
    if (localError) {
      setError(localError);
      return;
    }

    const baseUrl = getApiBaseUrl();
    if (!baseUrl) {
      setError("Не настроен адрес backend для Try-On workflow.");
      return;
    }

    const formData = new FormData();
    formData.append("human_photo", humanPhoto.file);
    formData.append("garment_photo", garmentPhoto.file);

    setIsSubmitting(true);
    try {
      const client = new WebApiClient(baseUrl);
      const created = await client.createTryOnJob(formData);
      const currentStatus = await client.getJobStatus(created.job_id);
      setStatus(currentStatus);

      if (currentStatus.status === "completed") {
        router.push(`/workspace/try-on/result?job_id=${encodeURIComponent(created.job_id)}`);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Try-On workflow не был создан.");
    } finally {
      setIsSubmitting(false);
    }
  }

  const canSubmit = Boolean(humanPhoto && garmentPhoto && !isSubmitting);

  return (
    <main className="flex h-full min-w-0 flex-col overflow-hidden bg-[var(--background)]">
      <div className="border-b border-[var(--border)] bg-[var(--surface)] px-5 py-4 lg:px-6">
        <h1 className="workspace-title font-[family-name:var(--font-manrope)]">Новая примерка</h1>
        <p className="workspace-subtitle mt-2 max-w-[760px] text-[var(--text-secondary)]">
          Загрузите фото человека и фото одежды. Backend создаст Try-On job и вернет статус workflow.
        </p>
      </div>

      <form className="min-h-0 flex-1 overflow-hidden p-5 lg:p-6" onSubmit={handleSubmit}>
        <section className="tryon-layout grid h-full min-w-0 gap-5 overflow-hidden">
          <div className="min-h-0 overflow-y-auto overflow-x-hidden">
            <div className="grid gap-5">
              <UploadPanel label="Фото человека" onChange={selectHumanPhoto} selected={humanPhoto} />
              <UploadPanel label="Фото одежды" onChange={selectGarmentPhoto} selected={garmentPhoto} />
            </div>
          </div>

          <div className="workspace-main min-h-0 min-w-0 overflow-y-auto overflow-x-hidden">
            <div className="result-card site-card flex min-w-0 items-center justify-center p-8 lg:p-10">
              {humanPhoto && garmentPhoto ? (
                <div className="grid w-full gap-5 md:grid-cols-2">
                  <img alt="Фото человека" className="h-[360px] rounded-[1.5rem] object-cover" src={humanPhoto.previewUrl} />
                  <img alt="Фото одежды" className="h-[360px] rounded-[1.5rem] object-cover" src={garmentPhoto.previewUrl} />
                </div>
              ) : (
                <ImagePlaceholder className="h-[360px] w-full" label="Ожидание материалов" />
              )}
            </div>
          </div>

          <aside className="workspace-status min-h-0 overflow-y-auto overflow-x-hidden pr-1">
            <div className="site-card flex min-h-0 flex-col justify-between p-6">
              <div>
                <h2 className="text-[1.35rem] font-semibold">Статус workflow</h2>
                <div className="mt-6 grid gap-4">
                  {(status?.status_history ?? []).map((event) => (
                    <div className="rounded-[1.2rem] bg-[var(--background)] p-4" key={`${event.status}-${event.occurred_at}`}>
                      <strong className="block text-[0.95rem]">{event.stage}</strong>
                      <p className="mt-1 text-[0.85rem] leading-6 text-[var(--text-secondary)]">{event.message}</p>
                    </div>
                  ))}
                  {!status ? (
                    <div className="rounded-[1.2rem] bg-[var(--background)] p-4 text-[0.9rem] text-[var(--text-secondary)]">
                      Job будет создан после загрузки двух изображений.
                    </div>
                  ) : null}
                </div>
              </div>

              <div className="mt-6">
                {error ? <p className="mb-4 rounded-2xl bg-[#fce8e6] px-5 py-4 text-sm font-medium text-[var(--error)]">{error}</p> : null}
                <div className="mb-4 flex items-center justify-between text-[0.95rem]">
                  <span className="text-[var(--text-secondary)]">Sandbox charge:</span>
                  <strong>0 кредитов</strong>
                </div>
                <SiteButton className="w-full" disabled={!canSubmit} type="submit" variant="violet">
                  {isSubmitting ? "Создаем job" : "Сгенерировать примерку"}
                </SiteButton>
              </div>
            </div>
          </aside>
        </section>
      </form>
    </main>
  );
}
```

- [ ] **Step 2: Render workflow from page**

Replace `apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx` with:

```typescript
import { TryOnWorkflow } from "@/features/workspace/try-on-workflow";

export default function WorkspaceNewTryOnPage() {
  return <TryOnWorkflow />;
}
```

- [ ] **Step 3: Run frontend checks**

Run:

```powershell
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
```

Expected: both pass.

- [ ] **Step 4: Commit Task 5**

Run:

```powershell
git add apps/web/src/features/workspace/try-on-workflow.tsx apps/web/src/app/(workspace)/workspace/try-on/new/page.tsx
git commit -m "feat: connect try-on creation screen to backend"
```

---

### Task 6: Try-On Result Page Integration

**Files:**
- Create: `apps/web/src/features/workspace/try-on-result.tsx`
- Modify: `apps/web/src/app/(workspace)/workspace/try-on/result/page.tsx`

- [ ] **Step 1: Create result component**

Create `apps/web/src/features/workspace/try-on-result.tsx`:

```typescript
"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ImagePlaceholder } from "@/components/site/image-placeholder";
import { SiteButton } from "@/components/site/site-button";
import type { TryOnResultResponse } from "@/lib/api/contracts";
import { WebApiClient } from "@/lib/api/client";

function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "";
}

export function TryOnResultView() {
  const searchParams = useSearchParams();
  const jobId = searchParams.get("job_id");
  const [response, setResponse] = useState<TryOnResultResponse | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function loadResult() {
      setError("");
      if (!jobId) {
        setError("Не указан job_id для результата примерки.");
        setIsLoading(false);
        return;
      }

      const baseUrl = getApiBaseUrl();
      if (!baseUrl) {
        setError("Не настроен адрес backend для результата Try-On.");
        setIsLoading(false);
        return;
      }

      try {
        const client = new WebApiClient(baseUrl);
        const result = await client.getJobResult(jobId);
        if (isMounted) setResponse(result);
      } catch (requestError) {
        if (isMounted) setError(requestError instanceof Error ? requestError.message : "Не удалось загрузить результат.");
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }

    void loadResult();

    return () => {
      isMounted = false;
    };
  }, [jobId]);

  if (isLoading) {
    return <main className="px-8 py-10 lg:px-16">Загружаем результат Try-On...</main>;
  }

  if (error) {
    return (
      <main className="px-8 py-10 lg:px-16">
        <div className="site-card p-8">
          <h1 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold">Результат недоступен</h1>
          <p className="mt-4 text-[var(--text-secondary)]">{error}</p>
          <SiteButton className="mt-8" href="/workspace/try-on/new" variant="primary">
            Создать новую примерку
          </SiteButton>
        </div>
      </main>
    );
  }

  if (!response || response.status === "not_ready") {
    return (
      <main className="px-8 py-10 lg:px-16">
        <div className="site-card p-8">
          <h1 className="font-[family-name:var(--font-manrope)] text-[3rem] font-bold">Workflow еще выполняется</h1>
          <p className="mt-4 text-[var(--text-secondary)]">
            Текущий статус: {response?.status === "not_ready" ? response.current_status : "unknown"}.
          </p>
          <SiteButton className="mt-8" href="/workspace/try-on/new" variant="secondary">
            Вернуться к примерке
          </SiteButton>
        </div>
      </main>
    );
  }

  const result = response.result;

  return (
    <main className="px-8 py-10 lg:px-16">
      <div className="flex flex-wrap items-start justify-between gap-6">
        <div>
          <h1 className="font-[family-name:var(--font-manrope)] text-[clamp(2.6rem,5vw,4.6rem)] font-bold tracking-[-0.04em]">
            Результат примерки
          </h1>
          <p className="mt-3 text-[1.2rem] text-[var(--text-secondary)]">Job {result.job_id}</p>
        </div>
        <SiteButton href="/workspace/history" variant="secondary">История</SiteButton>
      </div>

      <section className="mt-10 grid gap-8 xl:grid-cols-[1fr_330px]">
        <div>
          {result.result_image.url ? (
            <img alt={result.result_image.alt} className="h-[460px] w-full rounded-[2rem] object-cover" src={result.result_image.url} />
          ) : (
            <ImagePlaceholder className="h-[460px]" label={result.result_image.alt} />
          )}
          <div className="site-card mt-8 flex flex-wrap gap-4 p-6">
            <SiteButton href="/workspace/outfit-builder" icon="auto_fix_high" variant="soft">Подобрать образ</SiteButton>
            <SiteButton href="/workspace/similar" icon="search" variant="soft">Найти похожее</SiteButton>
          </div>
        </div>

        <div className="grid gap-8">
          <article className="rounded-[2rem] border border-[#c7b8ff] bg-[#ede6ff] p-6">
            <h2 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold text-[#2f2570]">Quality report</h2>
            <p className="mt-3 text-[var(--text-secondary)]">
              Verdict: {result.quality_report.verdict}. Confidence: {Math.round(result.quality_report.confidence * 100)}%.
            </p>
            <div className="mt-6 grid gap-4">
              {result.quality_report.checks.map((check) => (
                <div className="rounded-[1.5rem] bg-white px-5 py-4 text-[0.95rem]" key={check.name}>
                  <strong>{check.name}</strong>
                  <p className="mt-1 text-[var(--text-secondary)]">{check.message}</p>
                </div>
              ))}
            </div>
          </article>

          <article className="site-card p-6">
            <h2 className="font-[family-name:var(--font-manrope)] text-[2rem] font-bold">Комментарий стилиста</h2>
            <p className="mt-5 leading-8 text-[var(--text-secondary)]">{result.stylist_note}</p>
          </article>
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 2: Render result view from page**

Replace `apps/web/src/app/(workspace)/workspace/try-on/result/page.tsx` with:

```typescript
import { Suspense } from "react";
import { TryOnResultView } from "@/features/workspace/try-on-result";

export default function WorkspaceTryOnResultPage() {
  return (
    <Suspense fallback={<main className="px-8 py-10 lg:px-16">Загружаем результат Try-On...</main>}>
      <TryOnResultView />
    </Suspense>
  );
}
```

- [ ] **Step 3: Run frontend checks**

Run:

```powershell
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
```

Expected: both pass.

- [ ] **Step 4: Commit Task 6**

Run:

```powershell
git add apps/web/src/features/workspace/try-on-result.tsx apps/web/src/app/(workspace)/workspace/try-on/result/page.tsx
git commit -m "feat: connect try-on result screen to backend"
```

---

### Task 7: End-To-End Verification

**Files:**
- Verify only.

- [ ] **Step 1: Run backend Try-On tests**

Run:

```powershell
pytest tests/test_try_on_sandbox_lifecycle.py -q
```

Expected: pass.

- [ ] **Step 2: Run backend architecture guardrail**

Run:

```powershell
pytest tests/architecture/test_http_routes_no_main_dependency.py tests/architecture/test_runtime_agents_no_side_effects.py -q
```

Expected: pass.

- [ ] **Step 3: Run frontend static checks**

Run:

```powershell
npm --prefix apps/web run typecheck
npm --prefix apps/web run lint
npm --prefix apps/web run build
```

Expected: all pass.

- [ ] **Step 4: Run backend locally**

Run:

```powershell
$env:ENVIRONMENT='test'
$env:TELEGRAM_BOT_TOKEN='test-token'
$env:GCP_PROJECT_ID='test-project'
$env:PUBSUB_TOPIC_NAME='test-topic'
uvicorn src.main:app --host 127.0.0.1 --port 8080
```

Expected: backend starts at `http://127.0.0.1:8080`.

- [ ] **Step 5: Run frontend locally**

In a second PowerShell session:

```powershell
$env:NEXT_PUBLIC_API_BASE_URL='http://127.0.0.1:8080'
npm --prefix apps/web run dev
```

Expected: Next.js starts and prints a localhost URL.

- [ ] **Step 6: Manual workflow check**

Open the printed Next.js URL and navigate to `/workspace/try-on/new`.

Expected:

- Human and garment files can be selected.
- Local previews render.
- Submit creates a backend job.
- Status history is shown.
- Completed job navigates to `/workspace/try-on/result?job_id=...`.
- Result page renders the sandbox result contract.

- [ ] **Step 7: Final status check**

Run:

```powershell
git status --short
```

Expected: only files changed by this implementation plan are listed. If verification required code adjustments, repeat the relevant task checks and commit the exact adjusted files from that task.

---

## Self-Review

Spec coverage:

- Backend job API: Tasks 1, 2, 3.
- Multipart upload: Tasks 1, 3, 5.
- Backend validation: Tasks 1, 2, 3.
- In-memory repository: Task 2.
- Fake generation port: Task 2.
- Status polling and history: Tasks 2, 3, 5.
- Result contract: Tasks 2, 3, 6.
- Sandbox cost events: Tasks 1, 2, 3.
- Existing `apps/web` integration: Tasks 4, 5, 6.
- Verification: Task 7.

Scope exclusions are preserved:

- No GCS.
- No Firestore persistence.
- No Vertex or real AI generation.
- No Marketplace, Product Card, or Similar Search work.
- No real billing or credit deduction.

No placeholders are present. All implementation steps name concrete files, commands, and expected outcomes.
