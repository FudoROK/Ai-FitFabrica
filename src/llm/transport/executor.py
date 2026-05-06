from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, ValidationError

from ..core.request import LLMRequest
from .json_extract import extract_first_json_object
from .registry import get_schema
from .result import ExtractionResult


class LLMTransportExecutor:
    def __init__(self, provider, logger_: logging.Logger | None = None) -> None:
        self.provider = provider
        self.logger = logger_ or logging.getLogger(__name__)

    def run(self, task_name: str, prompt: str, *, strict: bool = True, soft: bool = True) -> ExtractionResult:
        schema_model, schema_version, postprocess = get_schema(task_name)
        last_raw: str | None = None
        error_type: str | None = None

        if strict:
            strict_result = self.provider.generate(
                LLMRequest(
                    task=task_name,
                    input=prompt,
                    structured_output={
                        "name": "payload",
                        "strict": True,
                        "schema": schema_model.model_json_schema(),
                    },
                    max_retries=1,
                )
            )
            if strict_result.status == "ok":
                try:
                    payload = strict_result.structured_data if isinstance(strict_result.structured_data, dict) else {}
                    data = self._validate_and_sanitize(payload, schema_model, postprocess, task_name)
                    return ExtractionResult(
                        status="success",
                        attempt="strict",
                        data=data,
                        confidence=float(data.get("confidence") or 0.0),
                        missing=[str(v) for v in (data.get("missing") or [])],
                        provider=getattr(self.provider, "provider_name", None),
                        task_name=task_name,
                        schema_version=schema_version,
                    )
                except (ValidationError, ValueError) as exc:
                    error_type = "schema_mismatch" if isinstance(exc, ValidationError) else "invalid_output"
                    self.logger.warning("llm_transport_strict_invalid", extra={"task": task_name, "error_type": error_type})
                    last_raw = strict_result.text
                else:
                    error_type = None
            else:
                error_type = strict_result.error.type if strict_result.error else "provider_error"
                last_raw = strict_result.text
        else:
            error_type = "strict_disabled"

        if soft:
            soft_prompt = self._build_soft_prompt(prompt, schema_model)
            soft_result = self.provider.generate(
                LLMRequest(
                    task=task_name,
                    input=soft_prompt,
                    max_retries=1,
                )
            )
            raw_text = soft_result.text or ""
            last_raw = raw_text or last_raw
            if soft_result.status == "ok":
                try:
                    json_block = extract_first_json_object(raw_text)
                    parsed = json.loads(json_block)
                    data = self._validate_and_sanitize(parsed, schema_model, postprocess, task_name)
                    return ExtractionResult(
                        status="partial",
                        attempt="soft",
                        data=data,
                        confidence=float(data.get("confidence") or 0.0),
                        missing=[str(v) for v in (data.get("missing") or [])],
                        provider=getattr(self.provider, "provider_name", None),
                        task_name=task_name,
                        schema_version=schema_version,
                        raw_response=self._truncate_raw(raw_text),
                    )
                except ValueError:
                    error_type = "json_parse_error"
                except ValidationError:
                    error_type = "schema_mismatch"
            else:
                error_type = soft_result.error.type if soft_result.error else "provider_error"

        return ExtractionResult(
            status="failed",
            attempt="quarantine",
            data={},
            confidence=0.0,
            missing=[],
            error_type=error_type,
            raw_response=self._truncate_raw(last_raw),
            provider=getattr(self.provider, "provider_name", None),
            task_name=task_name,
            schema_version=schema_version,
        )

    def _build_soft_prompt(self, prompt: str, schema_model: type[BaseModel]) -> str:
        fields: list[str] = []
        for name, field in schema_model.model_fields.items():
            fields.append(f"- {name}: {field.annotation}")
        return (
            "Return ONLY valid JSON.\n"
            "No markdown.\n"
            "All fields must be present.\n"
            "Use empty string for unknown values.\n"
            "missing must be an array of strings.\n"
            "confidence must be a number between 0 and 1.\n"
            "Schema:\n"
            + "\n".join(fields)
            + "\n\n"
            + prompt
        )

    def _validate_and_sanitize(
        self,
        payload: dict[str, Any],
        schema_model: type[BaseModel],
        postprocess,
        task_name: str,
    ) -> dict[str, Any]:
        validated = schema_model.model_validate(payload)
        data = validated.model_dump()
        cleaned = self._sanitize(data, parent_key=None, preserve_top_level_lead_patch=task_name == "profile_extract_task")
        if task_name == "profile_extract_task" and "lead_patch" not in cleaned:
            cleaned["lead_patch"] = {}
        if postprocess:
            cleaned = postprocess(cleaned)
        return cleaned

    def _sanitize(self, value: Any, *, parent_key: str | None, preserve_top_level_lead_patch: bool) -> Any:
        if isinstance(value, str):
            trimmed = value.strip()
            if not trimmed:
                return None
            return trimmed[:2000]
        if isinstance(value, dict):
            out: dict[str, Any] = {}
            for key, item in value.items():
                cleaned = self._sanitize(item, parent_key=str(key), preserve_top_level_lead_patch=preserve_top_level_lead_patch)
                if cleaned is None:
                    continue
                if (
                    isinstance(cleaned, dict)
                    and not cleaned
                    and not (preserve_top_level_lead_patch and parent_key is None and str(key) == "lead_patch")
                ):
                    continue
                out[str(key)] = cleaned
            return out
        if isinstance(value, list):
            items = [
                self._sanitize(item, parent_key=parent_key, preserve_top_level_lead_patch=preserve_top_level_lead_patch)
                for item in value
            ]
            return [item for item in items if item is not None]
        return value

    def _truncate_raw(self, value: str | None) -> str | None:
        if not value:
            return value
        return value[:20000]
