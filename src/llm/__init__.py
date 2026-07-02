from __future__ import annotations

from .llm_base_contracts import LLMMeta, LLMRequest, LLMResult, TaskName

__all__ = ["LLMService", "LLMMeta", "LLMRequest", "LLMResult", "TaskName"]


def __getattr__(name: str):
    """Keep package imports lightweight until the runtime service is actually requested."""
    if name == "LLMService":
        from .llm_service import LLMService

        return LLMService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
