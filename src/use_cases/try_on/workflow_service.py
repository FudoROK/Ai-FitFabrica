"""Application service facade for the Try-On sandbox lifecycle."""
from __future__ import annotations

from uuid import uuid4

from fastapi import UploadFile

from src.domain.try_on import (
    TryOnErrorCode,
    TryOnGenerationMode,
    TryOnJob,
    TryOnJobStatus,
    TryOnSandboxLifecycleMode,
    TryOnUploadRole,
)
from src.domain.billing import BillingOwnerType
from src.use_cases.try_on.ports import TryOnFileStoragePort, TryOnGenerationPort, TryOnJobRepositoryPort
from src.use_cases.try_on.ports import TryOnQualityVerifierPort, TryOnRepairPort, TryOnStylistPort
from .workflow_execution import execute_job as execute_try_on_job
from .workflow_job_factory import build_job, cost_event, status_event
from .workflow_models import TryOnUploadValidationConfig, TryOnValidationError
from .workflow_upload_validation import missing_fields, validate_upload, validation_error
from .outfit_composition_policy import evaluate_outfit_composition


class TryOnWorkflowService:
    """Coordinates validation, generation, cost recording, and job persistence."""

    def __init__(
        self,
        repository: TryOnJobRepositoryPort,
        generator: TryOnGenerationPort,
        analysis_bundle_service,
        instruction_creator,
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
        self._analysis_bundle_service = analysis_bundle_service
        self._instruction_creator = instruction_creator
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
        upper_garment_photo: UploadFile | None = None,
        lower_garment_photo: UploadFile | None = None,
        outerwear_garment_photo: UploadFile | None = None,
        full_body_garment_photo: UploadFile | None = None,
    ) -> TryOnJob:
        """Validate uploads, persist an accepted job, and return it for background execution."""
        required_fields = self._missing_fields(
            human_photo=human_photo,
            garment_photo=garment_photo,
            upper_garment_photo=upper_garment_photo,
            lower_garment_photo=lower_garment_photo,
            outerwear_garment_photo=outerwear_garment_photo,
            full_body_garment_photo=full_body_garment_photo,
        )
        if required_fields:
            raise self._validation_error(
                TryOnErrorCode.MISSING_REQUIRED_FILE,
                "Human photo and at least one garment photo are required.",
                {"fields": required_fields},
            )

        upload_roles = [
            (TryOnUploadRole.HUMAN_PHOTO, human_photo),
            (TryOnUploadRole.GARMENT_PHOTO, garment_photo),
            (TryOnUploadRole.UPPER_GARMENT_PHOTO, upper_garment_photo),
            (TryOnUploadRole.LOWER_GARMENT_PHOTO, lower_garment_photo),
            (TryOnUploadRole.OUTERWEAR_GARMENT_PHOTO, outerwear_garment_photo),
            (TryOnUploadRole.FULL_BODY_GARMENT_PHOTO, full_body_garment_photo),
        ]
        present_roles = [role for role, upload in upload_roles if upload is not None]
        outfit_verdict = evaluate_outfit_composition(present_roles)
        if outfit_verdict.decision == "block":
            raise self._validation_error(
                TryOnErrorCode.INVALID_GARMENT_COMBINATION,
                "Selected garment slots cannot be combined.",
                {
                    "reasons": outfit_verdict.reasons,
                    "warnings": outfit_verdict.warnings,
                    "roles": [role.value for role in present_roles],
                },
            )
        validated_uploads = [
            await self._validate_upload(role, upload)
            for role, upload in upload_roles
            if upload is not None
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
        return await execute_try_on_job(
            job=job,
            job_id=job_id,
            lifecycle_mode=lifecycle_mode,
            repository=self._repository,
            generator=self._generator,
            analysis_bundle_service=self._analysis_bundle_service,
            instruction_creator=self._instruction_creator,
            quality_verifier=self._quality_verifier,
            repair_adapter=self._repair_adapter,
            stylist_adapter=self._stylist_adapter,
            charge_completed_job=self._charge_completed_job,
        )

    async def get_job(self, job_id: str) -> TryOnJob | None:
        """Return a saved Try-On job, or None when the repository has no match."""
        return await self._repository.get(job_id)

    async def save_job(self, job: TryOnJob) -> None:
        """Persist a backend-updated Try-On job aggregate."""
        await self._repository.save(job)

    def _build_job(self, **kwargs) -> TryOnJob:
        """Build a Try-On job with common sandbox cost bookkeeping."""
        return build_job(
            generation_mode=getattr(self._generator, "generation_mode", TryOnGenerationMode.SANDBOX_FAKE),
            **kwargs,
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
        upper_garment_photo: UploadFile | None = None,
        lower_garment_photo: UploadFile | None = None,
        outerwear_garment_photo: UploadFile | None = None,
        full_body_garment_photo: UploadFile | None = None,
    ) -> list[str]:
        """Return request fields that did not include an upload."""
        return missing_fields(
            human_photo=human_photo,
            garment_photo=garment_photo,
            upper_garment_photo=upper_garment_photo,
            lower_garment_photo=lower_garment_photo,
            outerwear_garment_photo=outerwear_garment_photo,
            full_body_garment_photo=full_body_garment_photo,
        )

    async def _validate_upload(self, role: TryOnUploadRole, upload: UploadFile | None):
        """Read and validate upload bytes before returning metadata and payload."""
        return await validate_upload(role=role, upload=upload, validation=self._validation)

    def _status_event(self, status: TryOnJobStatus, message: str):
        """Build a status event with the canonical stage value."""
        return status_event(status, message)

    def _cost_event(self, *, estimated_units: int = 0, charged_credits: int = 0):
        """Build the canonical cost event for one Try-On sandbox generation."""
        return cost_event(estimated_units=estimated_units, charged_credits=charged_credits)

    def _validation_error(
        self,
        code: TryOnErrorCode,
        message: str,
        details: dict[str, object],
    ) -> TryOnValidationError:
        """Build a typed validation exception."""
        return validation_error(code=code, message=message, details=details)
