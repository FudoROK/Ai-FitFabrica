from __future__ import annotations

from dataclasses import dataclass

from .llm_base_contracts import TaskName
from .reply_task_contract import REPLY_RUNTIME_TASKS

_MEMORY_DAILY_RUNTIME_TASKS: frozenset[TaskName] = frozenset({"memory_daily_sync_task"})
_MEMORY_ROLLING_RUNTIME_TASKS: frozenset[TaskName] = frozenset({"memory_rolling_sync_task"})
_AGENT_RUNTIME_TASKS: frozenset[TaskName] = REPLY_RUNTIME_TASKS | frozenset({"profile_extract_task"})


@dataclass(frozen=True)
class ProviderRoutingDecision:
    path_name: str
    structured_provider_used: bool


def select_provider_path(task: TaskName) -> ProviderRoutingDecision:
    if task in _MEMORY_DAILY_RUNTIME_TASKS:
        return ProviderRoutingDecision(path_name="memory_daily_runtime", structured_provider_used=False)
    if task in _MEMORY_ROLLING_RUNTIME_TASKS:
        return ProviderRoutingDecision(path_name="memory_rolling_runtime", structured_provider_used=False)
    if task in _AGENT_RUNTIME_TASKS:
        return ProviderRoutingDecision(path_name="agent_runtime", structured_provider_used=False)
    return ProviderRoutingDecision(path_name="default", structured_provider_used=False)
