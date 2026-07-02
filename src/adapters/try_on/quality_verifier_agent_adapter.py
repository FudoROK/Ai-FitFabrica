"""Artifact-aware Quality Verifier agent adapter for Try-On workflows."""

from __future__ import annotations

from hashlib import sha256
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from src.adapters.storage.contracts import ObjectStorage
from src.adk_agents.quality_verifier_agent.contracts import QualityVerifierDecisionContract
from src.adk_agents.quality_verifier_agent.deploy_config import QualityVerifierAgentDeployConfig
from src.adk_agents.quality_verifier_agent.prompt_config import QUALITY_VERIFIER_INSTRUCTION
from src.domain.agent_runtime import AgentArtifactReference, AgentInvocationRequest, AgentRuntimeStatus, AgentValidationStatus
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnStoredInput,
)
from src.use_cases.agents.invocation_service import AgentInvocationService
from src.use_cases.try_on.ports import TryOnQualityVerifierPort
from src.use_cases.try_on.quality_policy import TryOnQualityPolicy

_VERIFIER_MAX_IMAGE_SIDE = 1600
_VERIFIER_MAX_IMAGE_BYTES = 4 * 1024 * 1024
_VERIFIER_JPEG_QUALITY = 88


class TryOnQualityVerifierAgentAdapter(TryOnQualityVerifierPort):
    """Run deterministic checks and then inspect source/result artifacts with the Quality Verifier Agent."""

    def __init__(
        self,
        *,
        baseline_verifier: TryOnQualityVerifierPort,
        object_storage: ObjectStorage,
        invocation_service: AgentInvocationService,
        timeout_seconds: float,
        preferred_model: str | None,
    ) -> None:
        """Store verifier dependencies and versioned agent config."""

        self._baseline_verifier = baseline_verifier
        self._object_storage = object_storage
        self._invocation_service = invocation_service
        self._timeout_seconds = timeout_seconds
        self._config = QualityVerifierAgentDeployConfig()
        self._preferred_model = preferred_model or self._config.model
        self._quality_policy = TryOnQualityPolicy(minimum_pass_confidence=0.8)

    async def verify(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> TryOnQualityReport:
        """Return a backend-safe report from deterministic and artifact-aware visual verification."""

        baseline_report = await self._baseline_verifier.verify(
            job_id=job_id,
            generation_mode=generation_mode,
            input_metadata=input_metadata,
            stored_inputs=stored_inputs,
            result=result,
        )
        if baseline_report.verdict == "reject" or result.result_image.kind != "generated_artifact":
            return baseline_report

        human_input = _stored_input_for_role(stored_inputs, "human_photo")
        garment_input = _first_garment_input(stored_inputs)
        generated_object_key = result.result_image._artifact_object_key
        if human_input is None or garment_input is None or not generated_object_key:
            return self._fallback_report(
                baseline_report=baseline_report,
                message="Quality Verifier Agent could not run because required source/result artifact references are missing.",
            )

        try:
            generated_reference = _generated_artifact_reference(
                object_storage=self._object_storage,
                object_key=generated_object_key,
            )
        except Exception as exc:  # noqa: BLE001
            return self._fallback_report(
                baseline_report=baseline_report,
                message=f"Quality Verifier Agent could not prepare the generated image artifact: {exc}",
            )
        envelope = await self._invocation_service.invoke(
            request=AgentInvocationRequest(
                agent_name=self._config.name,
                prompt_version=self._config.prompt_version,
                contract_version=self._config.contract_version,
                trace_id=job_id,
                prompt=QUALITY_VERIFIER_INSTRUCTION,
                input_payload={
                    "human_photo_object_key": human_input.object_key,
                    "garment_photo_object_key": garment_input.object_key,
                    "generated_image_object_key": generated_reference.object_key,
                    "approved_constraints": _approved_constraints(generation_mode=generation_mode),
                },
                artifact_references=[
                    _artifact_reference(human_input, purpose="human_photo"),
                    _artifact_reference(garment_input, purpose="garment_photo"),
                    generated_reference,
                ],
                response_schema=QualityVerifierDecisionContract.model_json_schema(),
                timeout_seconds=self._timeout_seconds,
                preferred_model=self._preferred_model,
            ),
            output_contract=QualityVerifierDecisionContract,
        )
        if (
            envelope.status != AgentRuntimeStatus.SUCCEEDED
            or envelope.validation_status != AgentValidationStatus.PASSED
            or envelope.output is None
        ):
            return self._fallback_report(
                baseline_report=baseline_report,
                message=(
                    envelope.error.message
                    if envelope.error is not None
                    else "Quality Verifier Agent did not return a validated decision."
                ),
            )

        try:
            decision = QualityVerifierDecisionContract.model_validate(envelope.output)
        except ValueError as exc:
            return self._fallback_report(
                baseline_report=baseline_report,
                message=f"Quality Verifier Agent returned an invalid decision: {exc}",
            )

        checks = list(baseline_report.checks)
        checks.extend(_category_score_checks(decision))
        checks.extend(_defect_checks(decision))
        checks.append(
            TryOnQualityCheck(
                name="model_backed_verdict",
                status="passed",
                confidence=decision.confidence,
                message=decision.summary,
            )
        )
        return self._quality_policy.evaluate(
            TryOnQualityReport(
                verdict=decision.verdict.value,
                confidence=decision.confidence,
                checks=checks,
                limitations=list(decision.limitations),
            )
        )

    def _fallback_report(self, *, baseline_report: TryOnQualityReport, message: str) -> TryOnQualityReport:
        """Fail closed to repair/review when visual verification cannot run."""

        checks = list(baseline_report.checks)
        checks.append(
            TryOnQualityCheck(
                name="quality_verifier_agent_unavailable",
                status="failed",
                confidence=0.55,
                message=message,
            )
        )
        return self._quality_policy.evaluate(
            TryOnQualityReport(
                verdict="reject",
                confidence=min(baseline_report.confidence, 0.79),
                checks=checks,
                limitations=[
                    *baseline_report.limitations,
                    "Artifact-aware visual quality verification was unavailable.",
                ],
            )
        )


def _stored_input_for_role(stored_inputs: list[TryOnStoredInput], role: str) -> TryOnStoredInput | None:
    """Return the first stored input matching one role value."""

    return next((item for item in stored_inputs if item.role.value == role and item.object_key), None)


def _first_garment_input(stored_inputs: list[TryOnStoredInput]) -> TryOnStoredInput | None:
    """Return the first available garment input for visual comparison."""

    return next((item for item in stored_inputs if item.role.value != "human_photo" and item.object_key), None)


def _artifact_reference(stored_input: TryOnStoredInput, *, purpose: str) -> AgentArtifactReference:
    """Map stored workflow input into an approved agent artifact reference."""

    return AgentArtifactReference(
        purpose=purpose,
        object_key=stored_input.object_key or "",
        content_type=stored_input.content_type,
        size_bytes=stored_input.size_bytes,
        sha256=stored_input.sha256,
    )


def _generated_artifact_reference(*, object_storage: ObjectStorage, object_key: str) -> AgentArtifactReference:
    """Build a deterministic artifact reference for the generated result."""

    object_key, payload, content_type = _normalized_generated_artifact(
        object_storage=object_storage,
        object_key=object_key,
        payload=object_storage.get_bytes(object_key),
    )
    return AgentArtifactReference(
        purpose="generated_result",
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(payload),
        sha256=sha256(payload).hexdigest(),
    )


def _normalized_generated_artifact(
    *,
    object_storage: ObjectStorage,
    object_key: str,
    payload: bytes,
) -> tuple[str, bytes, str]:
    """Return a visual-verifier-safe generated artifact, transcoding oversized images to JPEG."""

    original_content_type = _content_type_from_object_key(object_key)
    try:
        with Image.open(BytesIO(payload)) as opened:
            image = ImageOps.exif_transpose(opened)
            should_normalize = (
                original_content_type != "image/jpeg"
                or len(payload) > _VERIFIER_MAX_IMAGE_BYTES
                or max(image.size) > _VERIFIER_MAX_IMAGE_SIDE
            )
            if not should_normalize:
                return object_key, payload, original_content_type
            image.thumbnail((_VERIFIER_MAX_IMAGE_SIDE, _VERIFIER_MAX_IMAGE_SIDE))
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=_VERIFIER_JPEG_QUALITY, optimize=True)
    except UnidentifiedImageError:
        return object_key, payload, original_content_type

    normalized_payload = buffer.getvalue()
    normalized_key = _quality_verifier_generated_object_key(object_key)
    object_storage.put_bytes(
        object_key=normalized_key,
        payload=normalized_payload,
        content_type="image/jpeg",
    )
    return normalized_key, normalized_payload, "image/jpeg"


def _quality_verifier_generated_object_key(object_key: str) -> str:
    """Return a deterministic normalized artifact key next to the generated result."""

    parent = object_key.rsplit("/", 2)[0] if "/" in object_key else object_key
    return f"{parent}/quality_verifier/generated_result.jpg"


def _content_type_from_object_key(object_key: str) -> str:
    """Infer a safe image content type from a generated object key."""

    lowered = object_key.lower()
    if lowered.endswith(".jpg") or lowered.endswith(".jpeg"):
        return "image/jpeg"
    if lowered.endswith(".webp"):
        return "image/webp"
    return "image/png"


def _approved_constraints(*, generation_mode: TryOnGenerationMode) -> list[str]:
    """Return backend-owned quality requirements the agent must verify visually."""

    return [
        "Preserve human identity, face, body proportions, and pose.",
        "Preserve the garment color, silhouette, sleeves, collar, closure, pockets, logo, print, and texture cues.",
        "Reject extra hands, extra fingers, duplicated limbs, broken hands, broken neck, broken waist, and severe anatomy artifacts.",
        f"Generation backend: {generation_mode.value}.",
    ]


def _category_score_checks(decision: QualityVerifierDecisionContract) -> list[TryOnQualityCheck]:
    """Map category scores into quality checks."""

    return [
        TryOnQualityCheck(
            name=f"visual_category_{score.category}",
            status="passed" if score.score >= 0.8 else "warning",
            confidence=score.score,
            message=score.evidence,
        )
        for score in decision.category_scores
    ]


def _defect_checks(decision: QualityVerifierDecisionContract) -> list[TryOnQualityCheck]:
    """Map agent defects into fail-closed quality checks."""

    checks: list[TryOnQualityCheck] = []
    for defect in decision.defects:
        status = "failed" if defect.severity == "blocking" or not defect.repairable else "warning"
        checks.append(
            TryOnQualityCheck(
                name=f"visual_defect_{defect.defect_type}",
                status=status,
                confidence=defect.confidence,
                message=f"{decision.summary} Region: {defect.region}. Evidence: {defect.evidence}",
            )
        )
    return checks
