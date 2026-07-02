from __future__ import annotations

from importlib import import_module

__all__ = [
    "dialog_reply_task",
    "profile_extract_task",
]


_MODULE_MAP = {
    "dialog_reply_task": "src.llm.tasks.dialog_reply_task",
    "profile_extract_task": "src.llm.tasks.profile_extract_task",
}


def __getattr__(name: str):
    module_path = _MODULE_MAP.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(module_path)
    globals()[name] = module
    return module
