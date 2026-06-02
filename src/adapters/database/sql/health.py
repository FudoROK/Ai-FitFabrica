"""Health primitives for SQL infrastructure readiness."""


class SqlHealthcheck:
    """Carries SQL component identity and future health probe dependencies."""

    component_name = "postgresql"

    def __init__(self, engine) -> None:
        """Store the engine reference used by health checks."""
        self._engine = engine
