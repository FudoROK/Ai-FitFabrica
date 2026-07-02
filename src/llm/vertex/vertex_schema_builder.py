from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.domain.contracts.dialog_reply_output_contract import AgentOutput
from src.llm.contract_kinds import (
    REPLY_AGENT_OUTPUT_KIND,
    canonicalize_contract_kind,
)
from src.llm.reply_task_contract import CANONICAL_DIALOG_REPLY_TASK, normalize_reply_runtime_task

_ALLOWED_SCHEMA_KEYS = {
    "type",
    "properties",
    "required",
    "items",
    "enum",
    "anyOf",
    "nullable",
    "description",
    "propertyOrdering",
}

_JSON_TYPE_TO_VERTEX_TYPE = {
    "object": "OBJECT",
    "array": "ARRAY",
    "string": "STRING",
    "number": "NUMBER",
    "integer": "INTEGER",
    "boolean": "BOOLEAN",
}

_VERTEX_TYPES = set(_JSON_TYPE_TO_VERTEX_TYPE.values())


def _resolve_ref(ref: str, defs: dict[str, Any]) -> dict[str, Any]:
    prefix = "#/$defs/"
    if not ref.startswith(prefix):
        raise ValueError(f"Unsupported $ref path: {ref}")
    def_name = ref[len(prefix) :]
    resolved = defs.get(def_name)
    if not isinstance(resolved, dict):
        raise ValueError(f"Unable to resolve $ref: {ref}")
    return resolved


def _extract_nullable(branches: list[Any], defs: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    non_null: list[dict[str, Any]] = []
    nullable = False

    for raw_branch in branches:
        if not isinstance(raw_branch, dict):
            continue

        if raw_branch.get("type") == "null":
            nullable = True
            continue

        non_null.append(_convert_schema(raw_branch, defs))

    if len(non_null) == 1:
        return non_null[0], nullable

    merged_any_of = {"anyOf": non_null}
    return merged_any_of, nullable


def _convert_schema(raw_schema: dict[str, Any], defs: dict[str, Any]) -> dict[str, Any]:
    schema = deepcopy(raw_schema)

    if "$ref" in schema:
        resolved = _resolve_ref(str(schema["$ref"]), defs)
        schema.pop("$ref")
        schema = {**deepcopy(resolved), **schema}

    if "anyOf" in schema:
        collapsed, nullable = _extract_nullable(list(schema.get("anyOf") or []), defs)
        merged = {**collapsed, **{k: v for k, v in schema.items() if k != "anyOf"}}
        if nullable:
            merged["nullable"] = True
        schema = merged

    converted: dict[str, Any] = {}

    schema_type = schema.get("type")
    if isinstance(schema_type, str):
        converted_type = _JSON_TYPE_TO_VERTEX_TYPE.get(schema_type.lower())
        if converted_type is not None:
            converted["type"] = converted_type

    if isinstance(schema.get("description"), str):
        converted["description"] = schema["description"]

    if isinstance(schema.get("enum"), list):
        converted["enum"] = schema["enum"]

    if schema.get("nullable") is True:
        converted["nullable"] = True

    properties = schema.get("properties")
    if isinstance(properties, dict):
        converted_properties: dict[str, Any] = {}
        for prop_name, prop_schema in properties.items():
            if isinstance(prop_schema, dict):
                converted_properties[prop_name] = _convert_schema(prop_schema, defs)

        converted["properties"] = converted_properties
        converted["propertyOrdering"] = list(converted_properties.keys())

    required = schema.get("required")
    if isinstance(required, list):
        converted["required"] = [name for name in required if name in (converted.get("properties") or {})]

    items = schema.get("items")
    if isinstance(items, dict):
        converted["items"] = _convert_schema(items, defs)

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        converted["anyOf"] = [
            _convert_schema(branch, defs) for branch in any_of if isinstance(branch, dict)
        ]

    return {k: v for k, v in converted.items() if k in _ALLOWED_SCHEMA_KEYS}


def _build_vertex_schema_from_model(model: Any) -> dict[str, Any]:
    pydantic_schema = model.model_json_schema()
    defs = pydantic_schema.get("$defs")
    if not isinstance(defs, dict):
        defs = {}
    return _convert_schema(pydantic_schema, defs)


def _looks_like_vertex_schema(schema: dict[str, Any]) -> bool:
    schema_type = schema.get("type")
    return isinstance(schema_type, str) and schema_type in _VERTEX_TYPES


def _coerce_to_vertex_schema(schema: dict[str, Any]) -> dict[str, Any]:
    if _looks_like_vertex_schema(schema):
        return deepcopy(schema)

    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        defs = {}

    return _convert_schema(schema, defs)


def _default_contract_kind_for_task(task_name: str) -> str | None:
    normalized = normalize_reply_runtime_task(task_name)
    if normalized == CANONICAL_DIALOG_REPLY_TASK:
        return REPLY_AGENT_OUTPUT_KIND
    return None


def build_vertex_response_schema() -> dict[str, Any]:
    """Build Vertex-compatible response schema from canonical reply AgentOutput model."""
    return _build_vertex_schema_from_model(AgentOutput)


def build_vertex_structured_contract(
    *,
    task: str,
    structured_output: dict[str, Any] | None,
) -> dict[str, Any] | None:
    structured = structured_output if isinstance(structured_output, dict) else {}

    raw_kind = structured.get("kind")
    if raw_kind:
        canonical_kind = canonicalize_contract_kind(raw_kind)
    else:
        canonical_kind = _default_contract_kind_for_task(task)

    raw_schema = structured.get("schema")
    schema: dict[str, Any] | None
    if isinstance(raw_schema, dict):
        schema = _coerce_to_vertex_schema(raw_schema)
    elif canonical_kind == REPLY_AGENT_OUTPUT_KIND:
        schema = build_vertex_response_schema()
    else:
        schema = None

    if canonical_kind is None or not isinstance(schema, dict):
        return None

    return {
        "kind": canonical_kind,
        "schema": schema,
        "mime_type": structured.get("mime_type") or "application/json",
        "required": bool(structured.get("required", True)),
    }
