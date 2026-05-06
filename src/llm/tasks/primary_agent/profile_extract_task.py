from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, create_model

from ...core.result import LLMResult as CoreLLMResult
from ...transport.registry import register_schema
from src.domain.extraction import CANONICAL_PATCH_KEYS
from ..helpers.task_request_builder import ProviderRequestParts, ensure_ok_result


def _build_lead_patch_model() -> type[BaseModel]:
    field_definitions = {key: (str, ...) for key in CANONICAL_PATCH_KEYS}
    return create_model(
        "LeadPatch",
        __config__=ConfigDict(extra="forbid"),
        **field_definitions,
    )


LeadPatch = _build_lead_patch_model()


class LeadPatchPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lead_patch: LeadPatch
    missing: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


def register_profile_extract_schema() -> None:
    register_schema("profile_extract_task", LeadPatchPayload, schema_version="v3")


def lead_profile_schema() -> dict[str, Any]:
    lead_patch_properties = {key: {"type": "string"} for key in CANONICAL_PATCH_KEYS}
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "lead_patch": {
                "type": "object",
                "additionalProperties": False,
                "properties": lead_patch_properties,
                "required": list(CANONICAL_PATCH_KEYS),
            },
            "missing": {
                "type": "array",
                "items": {"type": "string"},
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
            },
        },
        "required": ["lead_patch", "missing", "confidence"],
    }


def _serialize_profile_extract_input(payload: dict[str, Any]) -> str:
    raw_context = {
        "user_message": payload.get("user_message") or "",
        "assistant_message": payload.get("assistant_message") or "",
        "history": payload.get("history") or [],
    }
    return json.dumps(raw_context, ensure_ascii=False)


def build_provider_request(payload: dict[str, Any], _meta) -> ProviderRequestParts:
    schema = lead_profile_schema()
    return ProviderRequestParts(
        model=payload["model"],
        instructions="",
        input=_serialize_profile_extract_input(payload),
        structured_output={
            "name": "lead_patch",
            "strict": True,
            "schema": schema,
        },
    )


def parse_provider_response(result: CoreLLMResult) -> dict[str, Any]:
    ready = ensure_ok_result(result)
    payload = ready.structured_data if isinstance(ready.structured_data, dict) else {}
    lead_patch = payload.get("lead_patch") if isinstance(payload.get("lead_patch"), dict) else {}
    canonical_patch = {key: str(lead_patch.get(key) or "") for key in CANONICAL_PATCH_KEYS}

    return {
        "profile": {
            "lead_patch": canonical_patch,
            "missing": [str(item) for item in (payload.get("missing") or [])],
            "confidence": float(payload.get("confidence") or 0.0),
        }
    }