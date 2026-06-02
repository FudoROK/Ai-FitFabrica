from __future__ import annotations

from src.llm.reply_task_contract import (
    CANONICAL_DIALOG_REPLY_TASK,
    REPLY_RUNTIME_TASKS,
    is_reply_runtime_task,
    normalize_reply_runtime_task,
)


def test_reply_task_contract_exposes_only_canonical_name() -> None:
    assert CANONICAL_DIALOG_REPLY_TASK == "dialog_reply_task"
    assert REPLY_RUNTIME_TASKS == frozenset({CANONICAL_DIALOG_REPLY_TASK})


def test_reply_task_normalization_keeps_canonical_name() -> None:
    assert normalize_reply_runtime_task(CANONICAL_DIALOG_REPLY_TASK) == CANONICAL_DIALOG_REPLY_TASK


def test_reply_task_detection_accepts_only_reply_runtime_names() -> None:
    assert is_reply_runtime_task(CANONICAL_DIALOG_REPLY_TASK) is True
    assert is_reply_runtime_task("legacy_reply_task") is False
    assert is_reply_runtime_task("profile_extract_task") is False
