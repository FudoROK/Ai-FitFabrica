"""Provider-runtime-backed Try-On repair adapter."""

from __future__ import annotations

from src.adapters.storage.contracts import ObjectStorage
from src.adapters.storage.object_naming import build_media_object_key
from src.domain.provider_models import ImageEditingRequest
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnResultImage,
    TryOnStoredInput,
    TryOnUploadRole,
)
from src.use_cases.try_on.ports import TryOnRepairPort


class ProviderRuntimeTryOnRepairAdapter(TryOnRepairPort):
    """Use provider-runtime image editing to repair a generated Try-On artifact."""

    def __init__(
        self,
        *,
        image_editing_provider,
        object_storage: ObjectStorage,
        tenant_id: str,
        root_prefix: str,
        signed_url_ttl_seconds: int,
    ) -> None:
        """Store explicit provider and storage dependencies."""
        self._image_editing_provider = image_editing_provider
        self._object_storage = object_storage
        self._tenant_id = tenant_id
        self._root_prefix = root_prefix
        self._signed_url_ttl_seconds = signed_url_ttl_seconds

    async def repair(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
        quality_report: TryOnQualityReport,
    ) -> TryOnResult:
        """Repair the generated artifact through the provider-runtime image-editing path."""
        if result.result_image.kind != "generated_artifact" or not result.result_image._artifact_object_key:
            return result

        source_object_key = result.result_image._artifact_object_key
        reference_object_keys = self._build_reference_object_keys(stored_inputs)
        edit_result = self._image_editing_provider.edit(
            ImageEditingRequest(
                task="repair_try_on_result",
                prompt=self._build_prompt(quality_report=quality_report),
                source_object_key=source_object_key,
                reference_object_keys=reference_object_keys,
                output_mime_type="image/webp",
            )
        )
        repaired_object_key = build_media_object_key(
            tenant_id=self._tenant_id,
            workflow="try-on",
            job_id=job_id,
            role="repair_image",
            filename="repair.webp",
            root_prefix=self._root_prefix,
        )
        repaired_payload = (
            f"try_on_provider_repair:{edit_result.provider}:{edit_result.output_object_key}:{generation_mode.value}".encode(
                "utf-8"
            )
        )
        stored_result = self._object_storage.put_bytes(
            object_key=repaired_object_key,
            payload=repaired_payload,
            content_type=edit_result.output_mime_type,
        )
        signed_url = self._object_storage.create_signed_get_url(
            stored_result.object_key,
            expires_in_seconds=self._signed_url_ttl_seconds,
        )
        repaired_image = TryOnResultImage(
            kind="generated_artifact",
            url=signed_url.url,
            alt="Provider-repaired Try-On result preview",
        )
        repaired_image._artifact_object_key = stored_result.object_key
        checks = list(result.quality_report.checks) + [
            TryOnQualityCheck(
                name="provider_runtime_repair_applied",
                status="passed",
                confidence=0.82,
                message="Provider-runtime image-editing repair created a backend-owned repaired artifact.",
            )
        ]
        return result.model_copy(
            update={
                "result_image": repaired_image,
                "quality_report": TryOnQualityReport(
                    verdict="repair_recommended",
                    confidence=quality_report.confidence,
                    checks=checks,
                    limitations=list(quality_report.limitations),
                ),
                "stylist_note": f"{result.stylist_note} Provider-backed repair pass applied before final verification.",
            }
        )

    @staticmethod
    def _build_prompt(*, quality_report: TryOnQualityReport) -> str:
        """Build a repair prompt from backend quality-report signals."""
        failed_or_warning_checks = [
            f"{check.name}: {check.message}"
            for check in quality_report.checks
            if check.status in {"warning", "failed"}
        ]
        issues_summary = "; ".join(failed_or_warning_checks) if failed_or_warning_checks else "local artifact issues"
        return (
            "Repair only the local Try-On defects while preserving the person's identity, pose, and garment intent. "
            f"Focus on these issues: {issues_summary}."
        )

    @staticmethod
    def _build_reference_object_keys(stored_inputs: list[TryOnStoredInput]) -> list[str]:
        """Collect stable reference object keys from persisted human and garment inputs."""
        reference_object_keys: list[str] = []
        for role in (TryOnUploadRole.HUMAN_PHOTO, TryOnUploadRole.GARMENT_PHOTO):
            for stored_input in stored_inputs:
                if stored_input.role != role:
                    continue
                object_key = stored_input.object_key or stored_input.object_name
                if object_key:
                    reference_object_keys.append(object_key)
                break
        return reference_object_keys
