"""Model-backed stylist note generation for completed Try-On results."""

from __future__ import annotations

import json

from src.domain.provider_models import StructuredReasoningRequest
from src.domain.try_on import (
    TryOnGenerationMode,
    TryOnInputMetadata,
    TryOnResult,
    TryOnStoredInput,
)
from src.use_cases.try_on.ports import TryOnStylistPort


class ModelBackedTryOnStylist(TryOnStylistPort):
    """Use structured reasoning to build the final user-facing stylist note."""

    def __init__(self, *, structured_reasoning_provider, fallback_stylist: TryOnStylistPort | None = None) -> None:
        """Store the provider and optional deterministic fallback stylist."""
        self._structured_reasoning_provider = structured_reasoning_provider
        self._fallback_stylist = fallback_stylist

    async def generate_note(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> str:
        """Return a provider-backed stylist note, or fall back to deterministic wording."""
        try:
            reasoning = self._structured_reasoning_provider.generate_structured(
                StructuredReasoningRequest(
                    task="try_on_stylist_note",
                    prompt=self._build_prompt(
                        job_id=job_id,
                        generation_mode=generation_mode,
                        input_metadata=input_metadata,
                        stored_inputs=stored_inputs,
                        result=result,
                    ),
                    response_schema={
                        "type": "object",
                        "properties": {
                            "note": {"type": "string"},
                        },
                        "required": ["note"],
                    },
                )
            )
            note = reasoning.payload.get("note")
        except Exception:  # noqa: BLE001
            note = None
        if isinstance(note, str) and note.strip():
            return note.strip()
        if self._fallback_stylist is not None:
            return await self._fallback_stylist.generate_note(
                job_id=job_id,
                generation_mode=generation_mode,
                input_metadata=input_metadata,
                stored_inputs=stored_inputs,
                result=result,
            )
        return "Try-On result is ready. Review fit, silhouette, and garment details against the original product before purchase."

    def _build_prompt(
        self,
        *,
        job_id: str,
        generation_mode: TryOnGenerationMode,
        input_metadata: list[TryOnInputMetadata],
        stored_inputs: list[TryOnStoredInput],
        result: TryOnResult,
    ) -> str:
        """Build the backend fact pack used to generate a concise stylist note."""
        facts = {
            "job_id": job_id,
            "generation_mode": generation_mode.value,
            "input_count": len(input_metadata),
            "stored_input_count": len(stored_inputs),
            "quality_verdict": result.quality_report.verdict,
            "quality_confidence": result.quality_report.confidence,
            "result_image_kind": result.result_image.kind,
            "existing_note": result.stylist_note,
        }
        return (
            "You are the final stylist explanation layer for a fashion Try-On workflow. "
            "Use only the provided backend facts. "
            "Return one concise user-facing note that explains the result carefully, without inventing garment facts. "
            f"Backend facts: {json.dumps(facts, ensure_ascii=False)}"
        )
