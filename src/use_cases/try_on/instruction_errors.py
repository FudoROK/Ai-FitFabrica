"""Safe failures for the mandatory Try-On instruction stage."""


class TryOnInstructionFailure(RuntimeError):
    """Fail-closed instruction creation failure safe for workflow mapping."""

    def __init__(self, *, safe_code: str = "try_on_instruction_failed") -> None:
        self.safe_code = safe_code
        super().__init__("Try-On instruction generation failed.")
