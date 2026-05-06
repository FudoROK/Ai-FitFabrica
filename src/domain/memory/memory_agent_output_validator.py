from __future__ import annotations

from typing import Any

from src.runtime_agents.memory_agent.memory_response_mapper import map_runtime_payload
from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract


class MemoryAgentOutputValidator:
    """Strict canonical validator for memory-agent structured output."""

    def validate(self, *, payload: Any) -> DailyMemoryContract:
        normalized_payload = map_runtime_payload(payload) if isinstance(payload, dict) else payload
        return DailyMemoryContract.model_validate(normalized_payload)
