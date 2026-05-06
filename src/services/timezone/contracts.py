from __future__ import annotations

from typing import Protocol

from .models import TimezoneResolutionInput, TimezoneResolutionResult


class TimezoneResolver(Protocol):
    def resolve(self, resolution_input: TimezoneResolutionInput) -> TimezoneResolutionResult:
        """Resolve timezone deterministically from normalized location attributes."""
