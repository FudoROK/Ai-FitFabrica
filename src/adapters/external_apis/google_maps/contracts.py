from __future__ import annotations

from typing import Optional, Protocol


class TimezoneResolverContract(Protocol):
    """Provider-agnostic contract for city+country -> IANA timezone resolution."""

    def resolve(self, city: str, country: str) -> Optional[str]:
        """Return IANA timezone name or None when resolution is not possible."""
