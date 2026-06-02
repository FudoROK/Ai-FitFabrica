from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol, runtime_checkable

from .llm_base_contracts import TaskName
from .core.result import LLMResult as CoreLLMResult
from .reply_task_contract import CANONICAL_DIALOG_REPLY_TASK
from .tasks import dialog_reply_task, memory_daily_sync_task, memory_rolling_sync_task, profile_extract_task
from .tasks.helpers.task_request_builder import ProviderRequestParts

BuildProviderRequestFn = Callable[[dict[str, Any], Any], ProviderRequestParts]
ParseProviderResponseFn = Callable[[CoreLLMResult], dict[str, Any]]


@runtime_checkable
class TaskModuleContract(Protocol):
    build_provider_request: BuildProviderRequestFn
    parse_provider_response: ParseProviderResponseFn


@dataclass(frozen=True)
class TaskDefinition:
    task_name: TaskName
    implementation: TaskModuleContract


TASK_REGISTRY: dict[TaskName, TaskDefinition] = {
    CANONICAL_DIALOG_REPLY_TASK: TaskDefinition(task_name=CANONICAL_DIALOG_REPLY_TASK, implementation=dialog_reply_task),
    "profile_extract_task": TaskDefinition(task_name="profile_extract_task", implementation=profile_extract_task),
    "memory_daily_sync_task": TaskDefinition(task_name="memory_daily_sync_task", implementation=memory_daily_sync_task),
    "memory_rolling_sync_task": TaskDefinition(task_name="memory_rolling_sync_task", implementation=memory_rolling_sync_task),
}


def _has_valid_contract(implementation: object) -> tuple[bool, str | None]:
    build_fn = getattr(implementation, "build_provider_request", None)
    parse_fn = getattr(implementation, "parse_provider_response", None)
    if not callable(build_fn):
        return False, "missing_callable:build_provider_request"
    if not callable(parse_fn):
        return False, "missing_callable:parse_provider_response"
    return True, None


def validate_task_registry() -> None:
    errors: list[str] = []
    for task_name, definition in TASK_REGISTRY.items():
        if definition.task_name != task_name:
            errors.append(f"task_name_mismatch:{task_name}->{definition.task_name}")
        is_valid, reason = _has_valid_contract(definition.implementation)
        if not is_valid:
            errors.append(f"{task_name}:{reason}")
    if errors:
        raise RuntimeError(f"invalid_llm_task_registry:{','.join(errors)}")


def get_task_implementation(task_name: TaskName) -> TaskModuleContract:
    definition = TASK_REGISTRY.get(task_name)
    if definition is None:
        raise KeyError(f"llm_task_not_registered:{task_name}")
    return definition.implementation
