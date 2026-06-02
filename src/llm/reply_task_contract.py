from __future__ import annotations

from .llm_base_contracts import TaskName

CANONICAL_DIALOG_REPLY_TASK: TaskName = "dialog_reply_task"
REPLY_RUNTIME_TASKS: frozenset[TaskName] = frozenset({CANONICAL_DIALOG_REPLY_TASK})


def is_reply_runtime_task(task_name: str) -> bool:
    """Return whether the task name belongs to the backend reply-runtime contour."""
    return str(task_name or "").strip() in REPLY_RUNTIME_TASKS


def normalize_reply_runtime_task(task_name: str) -> str:
    """Normalize reply-task names onto the canonical backend task name."""
    return str(task_name or "").strip()
