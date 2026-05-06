from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class TimezoneResolutionInput:
    city: Optional[str]
    country: Optional[str]
    timezone: Optional[str] = None


@dataclass(frozen=True)
class TimezoneResolutionResult:
    resolved: bool
    timezone: Optional[str]
    source: Literal[
        "user_explicit",
        "backend_resolved_from_city_country",
        "backend_resolved_from_city_only",
        "manual_override",
        "unknown",
    ]
    confidence: Optional[float]
    reason: str
    normalized_city: Optional[str] = None
    normalized_country: Optional[str] = None
