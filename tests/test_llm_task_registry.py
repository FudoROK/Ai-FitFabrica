from __future__ import annotations

import pytest

from src.llm.llm_task_registry import TASK_REGISTRY, get_task_implementation, validate_task_registry


EXPECTED_TASKS = {
    "dialog_reply_task",
    "profile_extract_task",
}


def test_task_registry_catalog_is_explicit_and_complete() -> None:
    assert set(TASK_REGISTRY.keys()) == EXPECTED_TASKS


def test_get_task_implementation_returns_contract_functions() -> None:
    implementation = get_task_implementation("dialog_reply_task")

    assert callable(getattr(implementation, "build_provider_request", None))
    assert callable(getattr(implementation, "parse_provider_response", None))


def test_validate_task_registry_fails_for_broken_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BrokenTask:
        def build_provider_request(self, payload, meta):  # noqa: ANN001, ANN201
            return payload, meta

    broken_registry = dict(TASK_REGISTRY)
    broken_registry["dialog_reply_task"] = broken_registry["dialog_reply_task"].__class__(
        task_name="dialog_reply_task",
        implementation=_BrokenTask(),
    )

    monkeypatch.setattr("src.llm.llm_task_registry.TASK_REGISTRY", broken_registry)

    with pytest.raises(RuntimeError, match="invalid_llm_task_registry:dialog_reply_task:missing_callable:parse_provider_response"):
        validate_task_registry()


def test_get_task_implementation_raises_for_unregistered_task() -> None:
    with pytest.raises(KeyError, match="llm_task_not_registered:unknown"):
        get_task_implementation("unknown")  # type: ignore[arg-type]
