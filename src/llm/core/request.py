from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class LLMArtifact:
    """Transient binary artifact passed only across the provider boundary."""

    purpose: str
    content_type: str
    payload: bytes


@dataclass(frozen=True)
class LLMRequest:
    task: str
    input: str
    artifacts: list[LLMArtifact] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    structured_output: Optional[dict[str, Any]] = None
    tool_capabilities: list[dict[str, Any]] = field(default_factory=list)
    model: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    timeout_s: Optional[int] = None
    max_retries: int = 0
    temperature: Optional[float] = None
