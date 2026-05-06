from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from src.runtime_agents.memory_agent.contracts.daily import DailyMemoryContract
from src.runtime_agents.memory_agent.contracts.rolling import RollingMemoryContract
from src.domain.memory.memory_agent_output_validator import MemoryAgentOutputValidator


_validator = MemoryAgentOutputValidator()


def parse_memory_output_payload(candidate_payload: Any) -> DailyMemoryContract:
    """Parse and validate memory agent payload into canonical typed output.""" 
    if isinstance(candidate_payload, DailyMemoryContract):
        return candidate_payload
    try:
        return _validator.validate(payload=candidate_payload)
    except ValidationError as exc:
        raise ValueError(f"memory_output_contract_invalid: {exc}") from exc

def parse_rolling_output_payload(candidate_payload: Any) -> RollingMemoryContract:
    """Parse and validate rolling memory agent payload into canonical typed output."""
    if isinstance(candidate_payload, RollingMemoryContract):
        return candidate_payload
    try:
        return RollingMemoryContract.model_validate(candidate_payload)
    except ValidationError as exc:
        raise ValueError(f"rolling_output_contract_invalid: {exc}") from exc
