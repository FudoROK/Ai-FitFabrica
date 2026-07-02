"""Safe failures exposed by Product Card generation adapters."""

from __future__ import annotations


class ProductCardGenerationFailure(RuntimeError):
    """Fail one Product Card generation without leaking provider details."""

    def __init__(self, *, safe_code: str) -> None:
        """Store one backend-safe error code."""
        super().__init__("Product Card generation failed.")
        self.safe_code = safe_code
