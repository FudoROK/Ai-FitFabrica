from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .contracts import FinalProfileInterface, SemanticValidationContext, ValidationError, ValidationResult


@dataclass(frozen=True)
class ReplyProfileOutput:
    reply_text: str
    system_payload: dict[str, Any] | None = None


class ReplyProfile(FinalProfileInterface[ReplyProfileOutput]):
    """Reply profile compute-only parser/validator without side effects."""

    def parse(self, raw_payload: Any) -> ReplyProfileOutput:
        payload = raw_payload if isinstance(raw_payload, dict) else {}
        reply_text = str(payload.get("reply_text") or "").strip()
        system_payload = payload.get("system_payload") if "system_payload" in payload else None
        return ReplyProfileOutput(
            reply_text=reply_text,
            system_payload=system_payload if isinstance(system_payload, dict) or system_payload is None else None,
        )

    def validate(self, typed_output: ReplyProfileOutput) -> ValidationResult:
        errors: list[ValidationError] = []
        if not isinstance(typed_output.reply_text, str):
            errors.append(ValidationError(code="reply_text_type", message="reply_text must be a string"))
        if typed_output.system_payload is not None and not isinstance(typed_output.system_payload, dict):
            errors.append(ValidationError(code="system_payload_type", message="system_payload must be an object|null"))
        return ValidationResult.success() if not errors else ValidationResult.failure(*errors)

    def semantic_validate(
        self,
        typed_output: ReplyProfileOutput,
        context: SemanticValidationContext,
    ) -> ValidationResult:
        _ = (typed_output, context)
        return ValidationResult.success()
