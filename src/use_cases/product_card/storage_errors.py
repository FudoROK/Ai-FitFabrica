"""Backend-owned error types for product-card storage failures."""


class ProductCardStorageError(RuntimeError):
    """Raised when source product-card assets cannot be persisted."""
