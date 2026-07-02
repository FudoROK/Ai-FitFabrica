"""Provider-runtime-backed Try-On repair adapter."""

from __future__ import annotations

from typing import Protocol

from src.adapters.storage.contracts import ObjectStorage
from src.adapters.storage.object_naming import build_media_object_key
from src.adk_agents.repair_agent.contracts import RepairInstructionContract
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
from src.use_cases.try_on.repair_policy import TryOnRepairPolicy


class RepairInstructionPlanner(Protocol):
    """Creates a backend-validated local repair plan before image editing."""

    async def create_plan(
        self,
        *,
        job_id: str,
        result: TryOnResult,
        quality_report: TryOnQualityReport,
    ) -> RepairInstructionContract:
        """Return one strict repair plan for the current result."""
        ...


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
        repair_instruction_planner: RepairInstructionPlanner | None = None,
    ) -> None:
        """Store explicit provider and storage dependencies."""
        self._image_editing_provider = image_editing_provider
        self._object_storage = object_storage
        self._tenant_id = tenant_id
        self._root_prefix = root_prefix
        self._signed_url_ttl_seconds = signed_url_ttl_seconds
        self._repair_instruction_planner = repair_instruction_planner
        self._repair_policy = TryOnRepairPolicy()

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
        repair_decision = self._repair_policy.evaluate(quality_report)
        if not repair_decision.allowed:
            blocked_report = quality_report.model_copy(
                update={
                    "verdict": "reject",
                    "checks": list(quality_report.checks)
                    + [
                        TryOnQualityCheck(
                            name="repair_policy_blocked",
                            status="failed",
                            confidence=1.0,
                            message=f"Repair was blocked by backend policy: {', '.join(repair_decision.rejection_reasons)}.",
                        )
                    ],
                }
            )
            return result.model_copy(update={"quality_report": blocked_report})
        if result.result_image.kind != "generated_artifact" or not result.result_image._artifact_object_key:
            return result
        if (
            generation_mode != TryOnGenerationMode.SANDBOX_FAKE
            and getattr(self._image_editing_provider, "provider_name", "") == "stub_image_editing"
        ):
            blocked_report = quality_report.model_copy(
                update={
                    "verdict": "reject",
                    "checks": list(quality_report.checks)
                    + [
                        TryOnQualityCheck(
                            name="repair_provider_not_production_ready",
                            status="failed",
                            confidence=1.0,
                            message="Stub image-editing repair is not allowed for real Try-On generation.",
                        )
                    ],
                    "limitations": list(quality_report.limitations)
                    + ["Real Try-On repair requires a production image-editing provider."],
                }
            )
            return result.model_copy(update={"quality_report": blocked_report})

        try:
            repair_plan = await self._create_repair_plan(
                job_id=job_id,
                result=result,
                quality_report=quality_report,
            )
        except Exception as exc:  # noqa: BLE001
            return result.model_copy(
                update={
                    "quality_report": self._repair_agent_unavailable_report(
                        quality_report=quality_report,
                        message=str(exc) or "Repair Agent planner failed.",
                    )
                }
            )
        if repair_plan is not None and repair_plan.repair_scope != "local":
            return result.model_copy(
                update={
                    "quality_report": self._blocked_by_repair_agent_report(
                        quality_report=quality_report,
                        repair_plan=repair_plan,
                    )
                }
            )

        source_object_key = result.result_image._artifact_object_key
        reference_object_keys = self._build_reference_object_keys(stored_inputs)
        edit_result = self._image_editing_provider.edit(
            ImageEditingRequest(
                task="repair_try_on_result",
                prompt=self._build_prompt(quality_report=quality_report, repair_plan=repair_plan),
                source_object_key=source_object_key,
                reference_object_keys=reference_object_keys,
                output_mime_type="image/png",
            )
        )
        repaired_object_key = build_media_object_key(
            tenant_id=self._tenant_id,
            workflow="try-on",
            job_id=job_id,
            role="repair_image",
            filename="repair.png",
            root_prefix=self._root_prefix,
        )
        repaired_payload = self._read_provider_output_bytes(
            provider=edit_result.provider,
            output_object_key=edit_result.output_object_key,
            generation_mode=generation_mode,
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

    async def _create_repair_plan(
        self,
        *,
        job_id: str,
        result: TryOnResult,
        quality_report: TryOnQualityReport,
    ) -> RepairInstructionContract | None:
        """Return an optional Repair Agent plan, failing closed when the planner errors."""

        if self._repair_instruction_planner is None:
            return None
        return await self._repair_instruction_planner.create_plan(
            job_id=job_id,
            result=result,
            quality_report=quality_report,
        )

    @staticmethod
    def _blocked_by_repair_agent_report(
        *,
        quality_report: TryOnQualityReport,
        repair_plan: RepairInstructionContract,
    ) -> TryOnQualityReport:
        """Return a reject report when the Repair Agent refuses local editing."""

        checks = list(quality_report.checks)
        checks.append(
            TryOnQualityCheck(
                name="repair_agent_blocked",
                status="failed",
                confidence=repair_plan.confidence,
                message=(
                    "Repair Agent marked local image editing unsafe: "
                    f"{'; '.join(repair_plan.limitations) or 'no safe local repair plan'}."
                ),
            )
        )
        return TryOnQualityReport(
            verdict="reject",
            confidence=min(quality_report.confidence, repair_plan.confidence),
            checks=checks,
            limitations=list(quality_report.limitations) + list(repair_plan.limitations),
        )

    @staticmethod
    def _repair_agent_unavailable_report(*, quality_report: TryOnQualityReport, message: str) -> TryOnQualityReport:
        """Return a reject report when the Repair Agent planner cannot run safely."""

        checks = list(quality_report.checks)
        checks.append(
            TryOnQualityCheck(
                name="repair_agent_unavailable",
                status="failed",
                confidence=0.0,
                message=f"Repair Agent planner failed before image editing: {message}.",
            )
        )
        return TryOnQualityReport(
            verdict="reject",
            confidence=0.0,
            checks=checks,
            limitations=list(quality_report.limitations) + ["Repair Agent planner was unavailable."],
        )

    def _read_provider_output_bytes(
        self,
        *,
        provider: str,
        output_object_key: str,
        generation_mode: TryOnGenerationMode,
    ) -> bytes:
        """Read real edited bytes, preserving stub compatibility for local tests."""
        if provider == "stub_image_editing":
            return f"try_on_provider_repair:{provider}:{output_object_key}:{generation_mode.value}".encode("utf-8")
        return self._object_storage.get_bytes(output_object_key)

    @staticmethod
    def _build_prompt(
        *,
        quality_report: TryOnQualityReport,
        repair_plan: RepairInstructionContract | None = None,
    ) -> str:
        """Build a repair prompt from backend quality-report signals."""
        failed_or_warning_checks = [
            f"{check.name}: {check.message}"
            for check in quality_report.checks
            if check.status in {"warning", "failed"}
        ]
        issues_summary = "; ".join(failed_or_warning_checks) if failed_or_warning_checks else "local artifact issues"
        prompt = (
            "Repair only the local Try-On defects while preserving the person's identity, pose, and garment intent. "
            f"Focus on these issues: {issues_summary}."
        )
        if repair_plan is None:
            return prompt
        plan_lines = [
            "Repair Agent approved local plan:",
            f"target issues: {', '.join(repair_plan.target_issues) or 'approved local defects'}",
            f"global instructions: {'; '.join(repair_plan.editing_instructions) or 'follow region instructions only'}",
        ]
        for instruction in repair_plan.region_instructions:
            preserve = f" preserve: {', '.join(instruction.preserve)}" if instruction.preserve else ""
            plan_lines.append(f"{instruction.region}: {instruction.instruction}.{preserve}")
        return f"{prompt} {' '.join(plan_lines)}"

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
