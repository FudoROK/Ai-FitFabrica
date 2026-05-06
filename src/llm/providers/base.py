from __future__ import annotations

from typing import Protocol

from ..core.request import LLMRequest
from ..core.result import LLMResult


class LLMProvider(Protocol):
    provider_name: str

    def generate(self, request: LLMRequest) -> LLMResult:
        ...
