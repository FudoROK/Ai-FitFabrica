from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from src.domain.contracts.primary_agent_output_contract import AgentOutput
from src.llm.vertex.vertex_schema_builder import build_vertex_response_schema


AGENT_OUTPUT_SCHEMA: dict[str, Any] = build_vertex_response_schema()


def validate_against_schema(payload: Any, schema: dict[str, Any], *, path: str = "$") -> tuple[bool, str | None]:
    schema_type = str(schema.get("type") or "").upper()
    nullable = bool(schema.get("nullable"))
    if payload is None:
        if nullable:
            return True, None
        return False, f"{path}: value is null but schema is not nullable"

    if schema_type == "OBJECT":
        if not isinstance(payload, dict):
            return False, f"{path}: expected object, got {type(payload).__name__}"
        required = schema.get("required") or []
        for key in required:
            if key not in payload:
                return False, f"{path}: missing required key '{key}'"
        properties = schema.get("properties") or {}
        additional_allowed = schema.get("additionalProperties", True)
        if additional_allowed is False:
            extra_keys = [key for key in payload.keys() if key not in properties]
            if extra_keys:
                return False, f"{path}: unexpected keys {extra_keys}"
        for key, value in payload.items():
            sub_schema = properties.get(key)
            if not isinstance(sub_schema, dict):
                continue
            ok, reason = validate_against_schema(value, sub_schema, path=f"{path}.{key}")
            if not ok:
                return False, reason
        return True, None

    if schema_type == "ARRAY":
        if not isinstance(payload, list):
            return False, f"{path}: expected array, got {type(payload).__name__}"
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, item in enumerate(payload):
                ok, reason = validate_against_schema(item, item_schema, path=f"{path}[{idx}]")
                if not ok:
                    return False, reason
        return True, None

    type_map: dict[str, type | tuple[type, ...]] = {
        "STRING": str,
        "NUMBER": (int, float),
        "INTEGER": int,
        "BOOLEAN": bool,
    }
    expected = type_map.get(schema_type)
    if expected is None:
        return True, None
    if isinstance(expected, tuple):
        if not isinstance(payload, expected) or isinstance(payload, bool):
            return False, f"{path}: expected {schema_type.lower()}, got {type(payload).__name__}"
        return True, None
    if not isinstance(payload, expected):
        return False, f"{path}: expected {schema_type.lower()}, got {type(payload).__name__}"
    return True, None


def validate_agent_output(payload: Any) -> tuple[bool, str | None]:
    try:
        AgentOutput.model_validate(payload)
    except ValidationError as exc:
        return False, str(exc)
    return True, None
