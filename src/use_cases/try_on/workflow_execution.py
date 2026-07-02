"""Execution-path helpers for the Try-On workflow service."""
from __future__ import annotations

from src.domain.try_on import (
    TryOnError,
    TryOnErrorCode,
    TryOnGenerationMode,
    TryOnJob,
    TryOnJobStatus,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnHumanIdentityVerdict,
    TryOnSandboxLifecycleMode,
    utc_now,
)
from src.use_cases.try_on.analysis_bundle_service import TryOnAnalysisBundle

from .workflow_job_factory import cost_event, repair_cost_event, status_event
from .analysis_errors import TryOnAnalysisBundleFailure
from .instruction_errors import TryOnInstructionFailure
from .quality_decision_policy import TryOnQualityDecision, TryOnQualityDecisionPolicy

_MAX_AUTO_RETRY_ATTEMPTS = 1


async def execute_job(
    *,
    job: TryOnJob,
    job_id: str,
    lifecycle_mode: TryOnSandboxLifecycleMode,
    repository,
    generator,
    analysis_bundle_service,
    instruction_creator,
    quality_verifier,
    repair_adapter,
    stylist_adapter,
    charge_completed_job,
) -> TryOnJob:
    """Execute one persisted Try-On job through the background worker path."""
    status_history = list(job.status_history)
    cost_events = list(job.cost_events)
    now = utc_now()

    if lifecycle_mode == TryOnSandboxLifecycleMode.PENDING:
        pending_job = job.model_copy(
            update={
                "status": TryOnJobStatus.ACCEPTED,
                "updated_at": now,
                "status_history": status_history,
                "cost_events": cost_events or [cost_event()],
                "result": None,
                "error": None,
            }
        )
        await repository.save(pending_job)
        return pending_job

    analysis_bundle = _analysis_bundle_from_job(job)
    if analysis_bundle is None:
        status_history.append(status_event(TryOnJobStatus.ANALYZING_HUMAN, "Analyzing human preservation constraints."))
        analyzing_job = job.model_copy(
            update={
                "status": TryOnJobStatus.ANALYZING_HUMAN,
                "updated_at": utc_now(),
                "status_history": status_history,
            }
        )
        await repository.save(analyzing_job)
        try:
            analysis_bundle = await analysis_bundle_service.analyze(
                job_id=job.job_id,
                stored_inputs=job.stored_inputs,
            )
        except TryOnAnalysisBundleFailure as exc:
            status_history.append(status_event(TryOnJobStatus.FAILED, "Required Try-On analysis failed."))
            failed_job = job.model_copy(
                update={
                    "status": TryOnJobStatus.FAILED,
                    "updated_at": utc_now(),
                    "status_history": status_history,
                    "cost_events": [cost_event(estimated_units=0, charged_credits=0)],
                    "result": None,
                    "error": TryOnError(
                        code=TryOnErrorCode.REQUIRED_ANALYSIS_FAILED,
                        message="Required analysis failed before Try-On generation.",
                        details={"job_id": job_id, "stage": "required_analysis_bundle", "failure_code": exc.safe_code},
                    ),
                }
            )
            await repository.save(failed_job)
            return failed_job
    human_identity_analysis = analysis_bundle.human_identity
    if human_identity_analysis.verdict != TryOnHumanIdentityVerdict.ALLOWED:
        status_history.append(status_event(TryOnJobStatus.FAILED, "Human photo is not suitable for Try-On generation."))
        failed_job = job.model_copy(
            update={
                "status": TryOnJobStatus.FAILED,
                "updated_at": utc_now(),
                "status_history": status_history,
                "cost_events": [cost_event(estimated_units=0, charged_credits=0)],
                "human_identity_analysis": human_identity_analysis,
                "result": None,
                "error": TryOnError(
                    code=TryOnErrorCode.HUMAN_IDENTITY_INPUT_NOT_SUITABLE,
                    message="Human photo is not suitable for Try-On generation.",
                    details={
                        "job_id": job_id,
                        "stage": "human_identity_analysis",
                        "rejection_reasons": human_identity_analysis.rejection_reasons,
                    },
                ),
            }
        )
        await repository.save(failed_job)
        return failed_job
    job = job.model_copy(
        update={
            "status": TryOnJobStatus.ANALYSIS_READY if lifecycle_mode == TryOnSandboxLifecycleMode.ANALYSIS_ONLY else job.status,
            "updated_at": utc_now(),
            "human_identity_analysis": human_identity_analysis,
            "garment_identity_analysis": analysis_bundle.garment_identity,
            "garment_slot_analyses": analysis_bundle.garment_slot_analyses,
            "material_texture_analysis": analysis_bundle.material_texture,
        }
    )
    if lifecycle_mode == TryOnSandboxLifecycleMode.ANALYSIS_ONLY:
        status_history.append(status_event(TryOnJobStatus.ANALYSIS_READY, "Input analysis is ready for user wear-control selection."))
        analysis_ready_job = job.model_copy(
            update={
                "status": TryOnJobStatus.ANALYSIS_READY,
                "updated_at": utc_now(),
                "status_history": status_history,
                "cost_events": cost_events or [cost_event(estimated_units=0, charged_credits=0)],
            }
        )
        await repository.save(analysis_ready_job)
        return analysis_ready_job
    await repository.save(job)
    try:
        instruction = await instruction_creator.create(
            job_id=job.job_id,
            analysis_bundle=analysis_bundle,
            wear_control_selections=job.wear_control_selections,
        )
    except TryOnInstructionFailure as exc:
        status_history.append(status_event(TryOnJobStatus.FAILED, "Try-On instruction generation failed."))
        failed_job = job.model_copy(
            update={
                "status": TryOnJobStatus.FAILED,
                "updated_at": utc_now(),
                "status_history": status_history,
                "cost_events": [cost_event(estimated_units=0, charged_credits=0)],
                "result": None,
                "error": TryOnError(
                    code=TryOnErrorCode.INSTRUCTION_GENERATION_FAILED,
                    message="Try-On instruction generation failed before image generation.",
                    details={"job_id": job_id, "stage": "try_on_instruction", "failure_code": exc.safe_code},
                ),
            }
        )
        await repository.save(failed_job)
        return failed_job
    job = job.model_copy(update={"instruction": instruction})
    await repository.save(job)
    generation_mode = getattr(generator, "generation_mode", job.generation_mode)
    status_history.append(
        status_event(
            TryOnJobStatus.GENERATING,
            _generation_message(generation_mode),
            generation_mode=generation_mode,
        )
    )
    if lifecycle_mode == TryOnSandboxLifecycleMode.FAILED:
        status_history.append(status_event(TryOnJobStatus.FAILED, "Try-On sandbox job failed."))
        failed_job = job.model_copy(
            update={
                "status": TryOnJobStatus.FAILED,
                "updated_at": utc_now(),
                "status_history": status_history,
                "cost_events": cost_events or [cost_event(generation_mode=generation_mode)],
                "result": None,
                "error": TryOnError(
                    code=TryOnErrorCode.JOB_FAILED,
                    message="Try-On sandbox job failed before result generation.",
                    details={"job_id": job_id, "stage": "sandbox_generation"},
                ),
            }
        )
        await repository.save(failed_job)
        return failed_job

    quality_decision_policy = TryOnQualityDecisionPolicy()
    generation_attempts = 0
    repair_attempts = 0
    retry_attempts = 0
    result = None
    verified_report = None
    quality_decision = None
    while True:
        generation_attempts += 1
        try:
            result = await generator.generate(
                job_id=job.job_id,
                input_metadata=job.input_metadata,
                stored_inputs=job.stored_inputs,
                instruction=instruction,
            )
        except Exception:
            status_history.append(status_event(TryOnJobStatus.FAILED, "Try-On generation failed."))
            failed_job = job.model_copy(
                update={
                    "status": TryOnJobStatus.FAILED,
                    "updated_at": utc_now(),
                    "status_history": status_history,
                    "cost_events": [
                        cost_event(
                            estimated_units=generation_attempts,
                            charged_credits=0,
                            generation_mode=generation_mode,
                        )
                    ],
                    "result": None,
                    "error": TryOnError(
                        code=TryOnErrorCode.GENERATION_FAILED,
                        message="Try-On generation failed before quality verification.",
                        details={
                            "job_id": job_id,
                            "stage": "try_on_generation",
                            "generation_mode": str(generation_mode),
                        },
                    ),
                }
            )
            await repository.save(failed_job)
            return failed_job
        status_history.append(status_event(TryOnJobStatus.QUALITY_CHECKING, "Checking generated result quality."))
        verified_report = (
            await quality_verifier.verify(
                job_id=job.job_id,
                generation_mode=generation_mode,
                input_metadata=job.input_metadata,
                stored_inputs=job.stored_inputs,
                result=result,
            )
            if quality_verifier is not None
            else result.quality_report
        )
        if lifecycle_mode == TryOnSandboxLifecycleMode.REPAIR_ACCEPTANCE and repair_attempts == 0:
            verified_report = _repair_acceptance_quality_report(verified_report)
        result = result.model_copy(update={"quality_report": verified_report})
        quality_decision = quality_decision_policy.evaluate(verified_report)
        if quality_decision.action == "repair" and repair_adapter is not None:
            status_history.append(status_event(TryOnJobStatus.REPAIRING, "Repairing generated Try-On result."))
            repair_attempts += 1
            result = await repair_adapter.repair(
                job_id=job.job_id,
                generation_mode=generation_mode,
                stored_inputs=job.stored_inputs,
                result=result,
                quality_report=verified_report,
            )
            if result.quality_report.verdict == "reject":
                verified_report = result.quality_report
            else:
                verified_report = (
                    await quality_verifier.verify(
                        job_id=job.job_id,
                        generation_mode=generation_mode,
                        input_metadata=job.input_metadata,
                        stored_inputs=job.stored_inputs,
                        result=result,
                    )
                    if quality_verifier is not None
                    else result.quality_report
                )
                if (
                    lifecycle_mode == TryOnSandboxLifecycleMode.REPAIR_ACCEPTANCE
                    and generation_mode == TryOnGenerationMode.SANDBOX_FAKE
                ):
                    verified_report = _repair_acceptance_final_quality_report(verified_report)
            result = result.model_copy(update={"quality_report": verified_report})
            quality_decision = quality_decision_policy.evaluate(verified_report)
        if quality_decision.action == "pass":
            break
        if quality_decision.action == "retry_recommended" and retry_attempts < _MAX_AUTO_RETRY_ATTEMPTS:
            retry_attempts += 1
            status_history.append(
                status_event(
                    TryOnJobStatus.GENERATING,
                    "Retrying Try-On generation after quality verifier found a system artifact.",
                    generation_mode=generation_mode,
                )
            )
            continue
        break
    if result is None or verified_report is None or quality_decision is None:
        raise RuntimeError("try_on_generation_loop_ended_without_quality_decision")
    if quality_decision.action != "pass":
        status_history.append(status_event(TryOnJobStatus.FAILED, "Try-On result rejected by quality verifier."))
        failed_job = job.model_copy(
            update={
                "status": TryOnJobStatus.FAILED,
                "updated_at": utc_now(),
                "status_history": status_history,
                "cost_events": [
                    cost_event(
                        estimated_units=generation_attempts,
                        charged_credits=0,
                        generation_mode=generation_mode,
                    ),
                    *_repair_cost_events(repair_attempts),
                ],
                "result": None,
                "error": TryOnError(
                    code=TryOnErrorCode.JOB_FAILED,
                    message="Try-On result was rejected by the quality verifier.",
                    details=_failed_quality_details(
                        job_id=job_id,
                        report=verified_report,
                        decision=quality_decision,
                        retry_attempts=retry_attempts,
                    ),
                ),
            }
        )
        await repository.save(failed_job)
        return failed_job
    if stylist_adapter is not None:
        stylist_note = await stylist_adapter.generate_note(
            job_id=job.job_id,
            generation_mode=generation_mode,
            input_metadata=job.input_metadata,
            stored_inputs=job.stored_inputs,
            result=result,
        )
        result = result.model_copy(update={"stylist_note": stylist_note})
    status_history.append(status_event(TryOnJobStatus.COMPLETED, "Try-On job completed."))
    charged_credits = await charge_completed_job(job_id=job.job_id)
    completed_job = job.model_copy(
        update={
            "status": TryOnJobStatus.COMPLETED,
            "updated_at": utc_now(),
            "status_history": status_history,
            "cost_events": [
                cost_event(
                    estimated_units=generation_attempts,
                    charged_credits=charged_credits,
                    generation_mode=generation_mode,
                ),
                *_repair_cost_events(repair_attempts),
            ],
            "human_identity_analysis": human_identity_analysis,
            "garment_identity_analysis": analysis_bundle.garment_identity,
            "garment_slot_analyses": analysis_bundle.garment_slot_analyses,
            "material_texture_analysis": analysis_bundle.material_texture,
            "result": result,
            "error": None,
        }
    )
    await repository.save(completed_job)
    return completed_job


def _generation_message(generation_mode: TryOnGenerationMode) -> str:
    """Return a user-safe status message for the active generation backend."""
    if generation_mode == TryOnGenerationMode.VERTEX_VIRTUAL_TRY_ON:
        return "Generating Vertex Virtual Try-On result."
    if generation_mode == TryOnGenerationMode.PROVIDER_RUNTIME:
        return "Generating provider-runtime Try-On result."
    return "Generating sandbox result."


def _repair_cost_events(repair_attempts: int) -> list:
    """Return provider image-editing repair cost events when repair was attempted."""
    if repair_attempts <= 0:
        return []
    return [repair_cost_event(estimated_units=repair_attempts, charged_credits=0)]


def _repair_acceptance_quality_report(report: TryOnQualityReport) -> TryOnQualityReport:
    """Force a local-repair quality report for deterministic staging acceptance."""
    checks = [
        TryOnQualityCheck(
            name="repair_acceptance_local_artifact",
            status="warning",
            confidence=0.82,
            message="Acceptance mode requests a deterministic local repair pass before final verification.",
        )
    ]
    return TryOnQualityReport(
        verdict="repair_recommended",
        confidence=min(report.confidence, 0.82),
        checks=checks,
        limitations=list(report.limitations) + ["Repair acceptance mode forced one local repair pass."],
    )


def _repair_acceptance_final_quality_report(report: TryOnQualityReport) -> TryOnQualityReport:
    """Return a sandbox-only pass report after the forced repair branch was exercised."""
    checks = [
        TryOnQualityCheck(
            name="repair_acceptance_final_verification",
            status="passed",
            confidence=0.91,
            message="Sandbox repair acceptance completed one repair pass before user exposure.",
        )
    ]
    return TryOnQualityReport(
        verdict="pass",
        confidence=max(report.confidence, 0.91),
        checks=checks,
        limitations=list(report.limitations) + ["Sandbox-only repair acceptance pass; not used for real AI output."],
    )


def _analysis_bundle_from_job(job: TryOnJob) -> TryOnAnalysisBundle | None:
    """Return a persisted analysis bundle when a job is resumed after user selection."""
    if (
        job.human_identity_analysis is None
        or job.garment_identity_analysis is None
        or not job.garment_slot_analyses
        or job.material_texture_analysis is None
    ):
        return None
    return TryOnAnalysisBundle(
        human_identity=job.human_identity_analysis,
        garment_identity=job.garment_identity_analysis,
        garment_slot_analyses=job.garment_slot_analyses,
        material_texture=job.material_texture_analysis,
    )


def _failed_quality_details(
    *,
    job_id: str,
    report: TryOnQualityReport,
    decision: TryOnQualityDecision,
    retry_attempts: int,
) -> dict[str, object]:
    """Return safe operator diagnostics for a failed quality gate."""
    return {
        "job_id": job_id,
        "stage": "quality_verifier",
        "verdict": report.verdict,
        "quality_decision": decision.model_dump(mode="json"),
        "retry_attempts": retry_attempts,
        "quality_confidence": report.confidence,
        "quality_checks": [check.model_dump(mode="json") for check in report.checks],
        "quality_limitations": list(report.limitations),
    }
