"""Shared cache helpers for runtime dependency facades."""
from __future__ import annotations

from typing import Callable, TypeVar

T = TypeVar("T")


def get_or_build_cached(settings, *, attr_name: str, builder: Callable[[], T]) -> T:
    """Return a cached settings-bound value or build and cache it."""
    value = getattr(settings, attr_name, None)
    if value is not None:
        return value
    value = builder()
    setattr(settings, attr_name, value)
    return value
