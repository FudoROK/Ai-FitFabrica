from __future__ import annotations

from typing import Final

REPLY_AGENT_OUTPUT_KIND: Final[str] = "reply_agent_output"


def canonicalize_contract_kind(contract_kind: str | None) -> str:
    raw_kind = str(contract_kind or "").strip()
    if not raw_kind:
        raise ValueError("contract routing violation: missing contract_kind")
    if raw_kind == REPLY_AGENT_OUTPUT_KIND:
        return raw_kind
    raise ValueError(
        "contract routing violation: unknown contract_kind "
        f"'{raw_kind}' (expected '{REPLY_AGENT_OUTPUT_KIND}')"
    )
