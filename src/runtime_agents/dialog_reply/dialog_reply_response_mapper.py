from __future__ import annotations

import json
import re
from typing import Any

_SENSITIVE_KEY_PATTERN = re.compile(r"(token|secret|password|api[_-]?key|authorization|auth)", re.IGNORECASE)


def map_to_runtime_payload(*, reply_text: str, system_payload: Any) -> dict[str, Any]:
    return {
        "reply_text": (reply_text or "").strip(),
        "system_payload": system_payload if isinstance(system_payload, dict) else {},
    }


def redact_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if _SENSITIVE_KEY_PATTERN.search(str(key)):
                redacted[str(key)] = "***REDACTED***"
            else:
                redacted[str(key)] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value


def build_parsed_payload_diagnostic(*, reply_text: str, system_payload: Any) -> str:
    payload_dict = system_payload if isinstance(system_payload, dict) else None
    lead_patch = payload_dict.get("lead_patch") if isinstance(payload_dict, dict) else None
    routing_decision = payload_dict.get("routing_decision") if isinstance(payload_dict, dict) else None
    lead_patch_keys = list(lead_patch.keys()) if isinstance(lead_patch, dict) else None

    diagnostic_payload = {
        "status": "ok",
        "reply_text": redact_sensitive(reply_text),
        "system_payload": redact_sensitive(payload_dict),
        "lead_patch": redact_sensitive(lead_patch),
        "lead_patch_keys": lead_patch_keys,
        "routing_decision": redact_sensitive(routing_decision),
    }
    return json.dumps(diagnostic_payload, ensure_ascii=False, default=str)
