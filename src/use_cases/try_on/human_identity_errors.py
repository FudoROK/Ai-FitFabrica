"""Typed safe failures for mandatory Human Identity analysis."""


class HumanIdentityAnalysisFailure(RuntimeError):
    """Safe failure raised when mandatory human analysis cannot complete."""

    def __init__(self, *, safe_code: str) -> None:
        """Store only the safe backend error code."""

        super().__init__("Human Identity analysis failed.")
        self.safe_code = safe_code
