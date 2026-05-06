from __future__ import annotations

from typing import Final

REPLY_AGENT_OUTPUT_KIND: Final[str] = "reply_agent_output"
MEMORY_AGENT_OUTPUT_KIND: Final[str] = "memory_agent_output"
MEMORY_DAILY_OUTPUT_KIND: Final[str] = "memory_daily_output"
MEMORY_ROLLING_OUTPUT_KIND: Final[str] = "memory_rolling_output"


def canonicalize_contract_kind(contract_kind: str | None) -> str:
    raw_kind = str(contract_kind or "").strip()
    if not raw_kind:
        raise ValueError("contract routing violation: missing contract_kind")
    if raw_kind in (REPLY_AGENT_OUTPUT_KIND, MEMORY_AGENT_OUTPUT_KIND, MEMORY_DAILY_OUTPUT_KIND, MEMORY_ROLLING_OUTPUT_KIND):
        return raw_kind
    raise ValueError(
        "contract routing violation: unknown contract_kind "
        f"'{raw_kind}' (expected one of '{REPLY_AGENT_OUTPUT_KIND}', '{MEMORY_AGENT_OUTPUT_KIND}', '{MEMORY_DAILY_OUTPUT_KIND}', '{MEMORY_ROLLING_OUTPUT_KIND}')"
    )
