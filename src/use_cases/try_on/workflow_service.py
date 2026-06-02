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
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnJob,
    TryOnJobStatus,
    TryOnResult,
    TryOnSandboxLifecycleMode,
    TryOnStoredInput,
    TryOnStatusEvent,
    TryOnUploadRole,
    TryOnWorkflowType,
    utc_now,
)
from src.domain.billing import BillingOwnerType
from src.use_cases.try_on.ports import TryOnFileStoragePort, TryOnGenerationPort, TryOnJobRepositoryPort
from src.use_cases.try_on.ports import TryOnQualityVerifierPort, TryOnRepairPort, TryOnStylistPort


@dataclass(frozen=True)
class TryOnUploadValidationConfig:
    """Validation limits for user-uploaded Try-On sandbox files."""

    allowed_content_types: set[str]
    max_upload_bytes: int


@dataclass(frozen=True)
class ValidatedTryOnUpload:
    """Validated upload bytes and sanitized metadata for one Try-On input."""

    metadata: TryOnInputMetadata
    payload: bytes


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
        file_storage: TryOnFileStoragePort,
        validation_config: TryOnUploadValidationConfig,
        quality_verifier: TryOnQualityVerifierPort | None = None,
        repair_adapter: TryOnRepairPort | None = None,
        stylist_adapter: TryOnStylistPort | None = None,
        billing_service=None,
        billing_owner_id: str = "public-person",
        billing_owner_type: BillingOwnerType = BillingOwnerType.PERSON,
    ) -> None:
        """Create the workflow service with explicit ports and validation rules."""
        self._repository = repository
        self._generator = generator
        self._quality_verifier = quality_verifier
        self._repair_adapter = repair_adapter
        self._stylist_adapter = stylist_adapter
        self._file_storage = file_storage
        self._validation = validation_config
        self._billing_service = billing_service
        self._billing_owner_id = billing_owner_id
        self._billing_owner_type = billing_owner_type

    async def create_job(
        self,
        human_photo: UploadFile | None,
        garment_photo: UploadFile | None,
    ) -> TryOnJob:
        """Validate uploads, persist an accepted job, and return it for background execution."""
        missing_fields = self._missing_fields(human_photo, garment_photo)
        if missing_fields:
            raise self._validation_error(
                TryOnErrorCode.MISSING_REQUIRED_FILE,
                "Human and garment photos are required.",
                {"fields": missing_fields},
            )

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
        job = self._build_job(
            job_id=job_id,
            status=TryOnJobStatus.ACCEPTED,
            input_metadata=input_metadata,
            stored_inputs=stored_inputs,
            status_history=[self._status_event(TryOnJobStatus.ACCEPTED, "Job accepted.")],
            result=None,
            error=None,
        )
        await self._repository.save(job)
        return job

    async def execute_job(
        self,
        *,
        job_id: str,
        lifecycle_mode: TryOnSandboxLifecycleMode = TryOnSandboxLifecycleMode.COMPLETE,
    ) -> TryOnJob:
        """Execute one persisted Try-On job through the background worker path."""
        lifecycle_mode = TryOnSandboxLifecycleMode(lifecycle_mode)
        job = await self._repository.get(job_id)
        if job is None:
            raise LookupError(f"Unknown Try-On job: {job_id}")

        status_history = list(job.status_history)
        cost_events = list(job.cost_events)
        now = utc_now()

        if lifecycle_mode == TryOnSandboxLifecycleMode.PENDING:
            pending_job = job.model_copy(
                update={
                    "status": TryOnJobStatus.ACCEPTED,
                    "updated_at": now,
                    "status_history": status_history,
                    "cost_events": cost_events or [self._cost_event()],
                    "result": None,
                    "error": None,
                }
            )
            await self._repository.save(pending_job)
            return pending_job

        status_history.append(self._status_event(TryOnJobStatus.GENERATING, "Generating sandbox result."))
        if lifecycle_mode == TryOnSandboxLifecycleMode.FAILED:
            status_history.append(self._status_event(TryOnJobStatus.FAILED, "Try-On sandbox job failed."))
            failed_job = job.model_copy(
                update={
                    "status": TryOnJobStatus.FAILED,
                    "updated_at": utc_now(),
                    "status_history": status_history,
                    "cost_events": cost_events or [self._cost_event()],
                    "result": None,
                    "error": TryOnError(
                        code=TryOnErrorCode.JOB_FAILED,
                        message="Try-On sandbox job failed before result generation.",
                        details={"job_id": job_id, "stage": "sandbox_generation"},
                    ),
                }
            )
            await self._repository.save(failed_job)
            return failed_job

        result = await self._generator.generate(
            job_id=job.job_id,
            input_metadata=job.input_metadata,
            stored_inputs=job.stored_inputs,
        )
        status_history.append(
            self._status_event(TryOnJobStatus.QUALITY_CHECKING, "Checking generated result quality.")
        )
        verified_report = (
            await self._quality_verifier.verify(
                job_id=job.job_id,
                generation_mode=getattr(self._generator, "generation_mode", job.generation_mode),
                input_metadata=job.input_metadata,
                stored_inputs=job.stored_inputs,
                result=result,
            )
            if self._quality_verifier is not None
            else result.quality_report
        )
        result = result.model_copy(update={"quality_report": verified_report})
        if verified_report.verdict == "repair_recommended" and self._repair_adapter is not None:
            status_history.append(self._status_event(TryOnJobStatus.REPAIRING, "Repairing generated Try-On result."))
            result = await self._repair_adapter.repair(
                job_id=job.job_id,
                generation_mode=getattr(self._generator, "generation_mode", job.generation_mode),
                stored_inputs=job.stored_inputs,
                result=result,
                quality_report=verified_report,
            )
            verified_report = (
                await self._quality_verifier.verify(
                    job_id=job.job_id,
                    generation_mode=getattr(self._generator, "generation_mode", job.generation_mode),
                    input_metadata=job.input_metadata,
                    stored_inputs=job.stored_inputs,
                    result=result,
                )
                if self._quality_verifier is not None
                else result.quality_report
            )
            result = result.model_copy(update={"quality_report": verified_report})
        if verified_report.verdict != "pass":
            status_history.append(self._status_event(TryOnJobStatus.FAILED, "Try-On result rejected by quality verifier."))
            failed_job = job.model_copy(
                update={
                    "status": TryOnJobStatus.FAILED,
                    "updated_at": utc_now(),
                    "status_history": status_history,
                    "cost_events": [self._cost_event(estimated_units=1, charged_credits=0)],
                    "result": None,
                    "error": TryOnError(
                        code=TryOnErrorCode.JOB_FAILED,
                        message="Try-On result was rejected by the quality verifier.",
                        details={"job_id": job_id, "stage": "quality_verifier", "verdict": verified_report.verdict},
                    ),
                }
            )
            await self._repository.save(failed_job)
            return failed_job
        if self._stylist_adapter is not None:
            stylist_note = await self._stylist_adapter.generate_note(
                job_id=job.job_id,
                generation_mode=getattr(self._generator, "generation_mode", job.generation_mode),
                input_metadata=job.input_metadata,
                stored_inputs=job.stored_inputs,
                result=result,
            )
            result = result.model_copy(update={"stylist_note": stylist_note})
        status_history.append(self._status_event(TryOnJobStatus.COMPLETED, "Try-On sandbox job completed."))
        charged_credits = await self._charge_completed_job(job_id=job.job_id)
        completed_job = job.model_copy(
            update={
                "status": TryOnJobStatus.COMPLETED,
                "updated_at": utc_now(),
                "status_history": status_history,
                "cost_events": [self._cost_event(estimated_units=1, charged_credits=charged_credits)],
                "result": result,
                "error": None,
            }
        )
        await self._repository.save(completed_job)
        return completed_job

    async def get_job(self, job_id: str) -> TryOnJob | None:
        """Return a saved Try-On job, or None when the repository has no match."""
        return await self._repository.get(job_id)

    def _build_job(
        self,
        job_id: str,
        status: TryOnJobStatus,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        status_history: list[TryOnStatusEvent],
        result: TryOnResult | None,
        error: TryOnError | None,
        charged_credits: int = 0,
    ) -> TryOnJob:
        """Build a Try-On job with common sandbox cost bookkeeping."""
        now = utc_now()
        return TryOnJob(
            job_id=job_id,
            workflow_type=TryOnWorkflowType.TRY_ON,
            generation_mode=getattr(self._generator, "generation_mode", TryOnGenerationMode.SANDBOX_FAKE),
            status=status,
            created_at=now,
            updated_at=now,
            input_metadata=input_metadata,
            stored_inputs=stored_inputs,
            status_history=status_history,
            cost_events=[self._cost_event(estimated_units=1 if status == TryOnJobStatus.COMPLETED else 0, charged_credits=charged_credits)],
            result=result,
            error=error,
        )

    async def _charge_completed_job(self, *, job_id: str) -> int:
        """Charge the completed Try-On job through the billing core when configured."""
        if self._billing_service is None:
            return 0
        ledger_event = await self._billing_service.charge_workflow(
            owner_id=self._billing_owner_id,
            owner_type=self._billing_owner_type,
            workflow_type="try_on",
            workflow_reference=job_id,
            stage_name="completed",
        )
        return max(0, -ledger_event.credits_delta)

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

    async def _validate_upload(self, role: TryOnUploadRole, upload: UploadFile | None) -> ValidatedTryOnUpload:
        """Read and validate upload bytes before returning metadata and payload."""
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

        metadata = TryOnInputMetadata(
            role=role,
            filename=upload.filename or role.value,
            content_type=content_type,
            size_bytes=size_bytes,
            sha256=sha256(payload).hexdigest(),
        )
        return ValidatedTryOnUpload(metadata=metadata, payload=payload)

    def _status_event(self, status: TryOnJobStatus, message: str) -> TryOnStatusEvent:
        """Build a status event with the canonical stage value."""
        stages = {
            TryOnJobStatus.ACCEPTED: "accepted",
            TryOnJobStatus.GENERATING: "sandbox_generation",
            TryOnJobStatus.QUALITY_CHECKING: "quality_check",
            TryOnJobStatus.REPAIRING: "repair",
            TryOnJobStatus.COMPLETED: "completed",
            TryOnJobStatus.FAILED: "failed",
        }
        return TryOnStatusEvent(status=status, stage=stages[status], message=message)

    def _cost_event(self, *, estimated_units: int = 0, charged_credits: int = 0) -> TryOnCostEvent:
        """Build the canonical cost event for one Try-On sandbox generation."""
        return TryOnCostEvent(
            event_type="try_on_sandbox_generation",
            estimated_units=estimated_units,
            charge_status=TryOnChargeStatus.CHARGED if charged_credits > 0 else TryOnChargeStatus.NOT_CHARGED,
            charged_credits=charged_credits,
        )

    def _validation_error(
        self,
        code: TryOnErrorCode,
        message: str,
        details: dict[str, object],
    ) -> TryOnValidationError:
        """Build a typed validation exception."""
        return TryOnValidationError(TryOnError(code=code, message=message, details=details))
