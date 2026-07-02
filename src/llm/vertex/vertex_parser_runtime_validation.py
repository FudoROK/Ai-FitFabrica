"""Runtime contract validation for parsed Vertex payloads."""
from __future__ import annotations

from typing import Any


def validate_runtime_contract(*, contract_kind: str | None, payload: dict[str, Any]) -> bool:
    _ = contract_kind
    return isinstance(payload.get("reply_text"), str) and isinstance(payload.get("system_payload"), dict)
