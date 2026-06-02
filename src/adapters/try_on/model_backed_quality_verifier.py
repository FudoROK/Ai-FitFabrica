"""Model-backed Try-On quality verifier built on structured reasoning."""

from __future__ import annotations

import json

from src.domain.provider_models import StructuredReasoningRequest
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnQualityCheck,
    TryOnQualityReport,
    TryOnResult,
    TryOnStoredInput,
)
from src.use_cases.try_on.ports import TryOnQualityVerifierPort


class ModelBackedTryOnQualityVerifier(TryOnQualityVerifierPort):
    """Use provider-backed structured reasoning to decide pass/repair/reject from backend facts."""

    def __init__(self, *, baseline_verifier: TryOnQualityVerifierPort, structured_reasoning_provider) -> None:
        """Store the deterministic verifier and structured reasoning provider dependencies."""
        self._baseline_verifier = baseline_verifier
        self._structured_reasoning_provider = structured_reasoning_provider

    async def verify(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> TryOnQualityReport:
        """Combine deterministic backend facts with a structured provider verdict."""
        baseline_report = await self._baseline_verifier.verify(
            job_id=job_id,
            generation_mode=generation_mode,
            input_metadata=input_metadata,
            stored_inputs=stored_inputs,
            result=result,
        )
        try:
            reasoning = self._structured_reasoning_provider.generate_structured(
                StructuredReasoningRequest(
                    task="try_on_quality_verification",
                    prompt=self._build_prompt(
                        job_id=job_id,
                        generation_mode=generation_mode,
                        baseline_report=baseline_report,
                        input_metadata=input_metadata,
                        stored_inputs=stored_inputs,
                        result=result,
                    ),
                    response_schema={
                        "type": "object",
                        "properties": {
                            "verdict": {"type": "string"},
                            "confidence": {"type": "number"},
                            "summary": {"type": "string"},
                            "limitations": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["verdict", "confidence", "summary", "limitations"],
                    },
                )
            )
            payload = reasoning.payload
        except Exception as exc:  # noqa: BLE001
            return self._fallback_report(baseline_report=baseline_report, exc=exc)
        verdict = payload.get("verdict")
        confidence = payload.get("confidence")
        summary = payload.get("summary")
        limitations = payload.get("limitations")
        if verdict not in {"pass", "repair_recommended", "reject"}:
            verdict = baseline_report.verdict
        if not isinstance(confidence, (int, float)):
            confidence = baseline_report.confidence
        if not isinstance(summary, str) or not summary.strip():
            summary = "Structured reasoning provider returned no verifier summary."
        if not isinstance(limitations, list) or not all(isinstance(item, str) for item in limitations):
            limitations = list(baseline_report.limitations)
        checks = list(baseline_report.checks) + [
            TryOnQualityCheck(
                name="model_backed_verdict",
                status="passed",
                confidence=max(0.0, min(1.0, float(confidence))),
                message=summary,
            )
        ]
        return TryOnQualityReport(
            verdict=verdict,
            confidence=max(0.0, min(1.0, float(confidence))),
            checks=checks,
            limitations=limitations,
        )

    def _fallback_report(self, *, baseline_report: TryOnQualityReport, exc: Exception) -> TryOnQualityReport:
        """Return the baseline report when the structured verifier provider is unavailable."""
        checks = list(baseline_report.checks) + [
            TryOnQualityCheck(
                name="model_backed_verifier_fallback",
                status="warning",
                confidence=0.55,
                message=f"Structured verifier backend was unavailable; falling back to deterministic verification: {exc}",
            )
        ]
        limitations = list(baseline_report.limitations) + [
            "Structured quality reasoning was unavailable, so the backend used deterministic verification only."
        ]
        return TryOnQualityReport(
            verdict=baseline_report.verdict,
            confidence=baseline_report.confidence,
            checks=checks,
            limitations=limitations,
        )

    def _build_prompt(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        baseline_report: TryOnQualityReport,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> str:
        """Build a deterministic backend fact pack for the structured quality-verifier decision."""
        facts = {
            "job_id": job_id,
            "generation_mode": generation_mode.value,
            "input_count": len(input_metadata),
            "stored_input_count": len(stored_inputs),
            "result_image_kind": result.result_image.kind,
            "baseline_verdict": baseline_report.verdict,
            "baseline_confidence": baseline_report.confidence,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status,
                    "confidence": check.confidence,
                    "message": check.message,
                }
                for check in baseline_report.checks
            ],
            "limitations": list(baseline_report.limitations),
        }
        return (
            "You are the backend quality verifier for a fashion Try-On workflow. "
            "Use only the provided backend facts. "
            "Return one verdict from: pass, repair_recommended, reject. "
            "Use repair_recommended only when the issue appears local and fixable. "
            "Use reject when the result should not be shown even after a local fix attempt. "
            f"Backend facts: {json.dumps(facts, ensure_ascii=False)}"
        )
