"""Application service for the Try-On sandbox lifecycle."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from uuid import uuid4

from fastapi import UploadFile

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
    """Validation limits for user-uploaded Try-On sandbox files."""

    allowed_content_types: set[str]
    max_upload_bytes: int


class TryOnValidationError(Exception):
    """Exception carrying a structured Try-On validation error."""

    def __init__(self, error: TryOnError) -> None:
        """Create an exception safe to map into an API error response."""
        super().__init__(error.message)
        self.error = error


class TryOnWorkflowService:
    """Coordinates validation, generation, cost recording, and job persistence."""

    def __init__(
        self,
        repository: TryOnJobRepositoryPort,
        generator: TryOnGenerationPort,
        validation: TryOnUploadValidationConfig,
    ) -> None:
        """Create the workflow service with explicit ports and validation rules."""
        self._repository = repository
        self._generator = generator
        self._validation = validation

    async def create_job(
        self,
        human_photo: UploadFile | None,
        garment_photo: UploadFile | None,
    ) -> TryOnJob:
        """Validate uploads, complete the sandbox generation workflow, and save the job."""
        missing_fields = self._missing_fields(human_photo, garment_photo)
        if missing_fields:
            raise self._validation_error(
                TryOnErrorCode.MISSING_REQUIRED_FILE,
                "Human and garment photos are required.",
                {"fields": missing_fields},
            )

        status_history = [
            self._status_event(TryOnJobStatus.ACCEPTED, "Job accepted."),
            self._status_event(TryOnJobStatus.VALIDATING_INPUTS, "Validating input files."),
        ]
        input_metadata = [
            await self._extract_metadata(TryOnUploadRole.HUMAN_PHOTO, human_photo),
            await self._extract_metadata(TryOnUploadRole.GARMENT_PHOTO, garment_photo),
        ]
        job_id = f"try_on_{uuid4().hex}"

        status_history.append(self._status_event(TryOnJobStatus.GENERATING, "Generating sandbox result."))
        result = await self._generator.generate(job_id=job_id, input_metadata=input_metadata)
        status_history.append(
            self._status_event(TryOnJobStatus.QUALITY_CHECKING, "Checking generated result quality.")
        )
        status_history.append(self._status_event(TryOnJobStatus.COMPLETED, "Try-On sandbox job completed."))

        now = utc_now()
        job = TryOnJob(
            job_id=job_id,
            workflow_type=TryOnWorkflowType.TRY_ON,
            status=TryOnJobStatus.COMPLETED,
            created_at=now,
            updated_at=now,
            input_metadata=input_metadata,
            status_history=status_history,
            cost_events=[
                TryOnCostEvent(
                    event_type="try_on_sandbox_generation",
                    estimated_units=1,
                    charge_status=TryOnChargeStatus.NOT_CHARGED,
                    charged_credits=0,
                )
            ],
            result=result,
            error=None,
        )
        await self._repository.save(job)
        return job

    async def get_job(self, job_id: str) -> TryOnJob | None:
        """Return a saved Try-On job, or None when the repository has no match."""
        return await self._repository.get(job_id)

    def _missing_fields(
        self,
        human_photo: UploadFile | None,
        garment_photo: UploadFile | None,
    ) -> list[str]:
        """Return request fields that did not include an upload."""
        fields: list[str] = []
        if human_photo is None:
            fields.append(TryOnUploadRole.HUMAN_PHOTO.value)
        if garment_photo is None:
            fields.append(TryOnUploadRole.GARMENT_PHOTO.value)
        return fields

    async def _extract_metadata(self, role: TryOnUploadRole, upload: UploadFile | None) -> TryOnInputMetadata:
        """Read and validate upload bytes before returning sanitized metadata."""
        if upload is None:
            raise self._validation_error(
                TryOnErrorCode.MISSING_REQUIRED_FILE,
                "Required upload is missing.",
                {"fields": [role.value]},
            )

        content_type = upload.content_type or ""
        if content_type not in self._validation.allowed_content_types:
            raise self._validation_error(
                TryOnErrorCode.UNSUPPORTED_CONTENT_TYPE,
                "Upload content type is not supported.",
                {
                    "field": role.value,
                    "content_type": content_type,
                    "allowed_content_types": sorted(self._validation.allowed_content_types),
                },
            )

        await upload.seek(0)
        payload = await upload.read()
        await upload.seek(0)
        size_bytes = len(payload)
        if size_bytes == 0:
            raise self._validation_error(
                TryOnErrorCode.EMPTY_FILE,
                "Uploaded file is empty.",
                {"field": role.value},
            )
        if size_bytes > self._validation.max_upload_bytes:
            raise self._validation_error(
                TryOnErrorCode.FILE_TOO_LARGE,
                "Uploaded file exceeds the configured size limit.",
                {
                    "field": role.value,
                    "size_bytes": size_bytes,
                    "max_upload_bytes": self._validation.max_upload_bytes,
                },
            )

        return TryOnInputMetadata(
            role=role,
            filename=upload.filename or role.value,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=sha256(payload).hexdigest(),
        )

    def _status_event(self, status: TryOnJobStatus, message: str) -> TryOnStatusEvent:
        """Build a status event with the canonical stage value."""
        return TryOnStatusEvent(status=status, stage=status.value, message=message)

    def _validation_error(
        self,
        code: TryOnErrorCode,
        message: str,
        details: dict[str, object],
    ) -> TryOnValidationError:
        """Build a typed validation exception."""
        return TryOnValidationError(TryOnError(code=code, message=message, details=details))
