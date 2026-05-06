from __future__ import annotations

from typing import Any


def map_runtime_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return payload
    # Canonical contract path: runtime accepts payload shape as-is and does not
    # inject/reshape content fields.
    return dict(payload)
