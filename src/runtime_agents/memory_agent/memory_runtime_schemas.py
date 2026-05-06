from __future__ import annotations

"""Compatibility re-exports for runtime memory contracts.

Canonical definitions are split into dedicated modules:
- daily: src.runtime_agents.memory_agent.contracts.daily
- rolling: src.runtime_agents.memory_agent.contracts.rolling
"""

from .contracts.base import StrictContractModel as StrictBaseModel
from .contracts.daily import (
    ActiveWindowUpdate,
    ConversationStateUpdate,
    DailyMemoryContract,
    DailyMemoryInputContract,
    DailySummaryPayload,
)
from .contracts.rolling import RollingMemoryContract, RollingMemoryInputContract, RollingUpdatePayload

__all__ = [
    "StrictBaseModel",
    "ActiveWindowUpdate",
    "DailySummaryPayload",
    "ConversationStateUpdate",
    "DailyMemoryInputContract",
    "DailyMemoryContract",
    "RollingUpdatePayload",
    "RollingMemoryInputContract",
    "RollingMemoryContract",
]
