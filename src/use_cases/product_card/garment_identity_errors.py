"""Safe failures exposed by Product Card Garment Identity analysis."""

from __future__ import annotations


class GarmentIdentityAnalysisFailure(RuntimeError):
    """Fail one garment analysis without leaking provider details."""

    def __init__(self, *, safe_code: str) -> None:
        """Store one backend-safe error code."""
        super().__init__("Garment Identity analysis failed.")
        self.safe_code = safe_code
