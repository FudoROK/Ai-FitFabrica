from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional


class CalendarContract(ABC):
    @abstractmethod
    def list_events(self, *, start_iso: str, end_iso: str) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def create_booking(self, *, payload: dict[str, Any]) -> Optional[str]:
        raise NotImplementedError

    @abstractmethod
    def reschedule_booking(self, *, booking_id: str, payload: dict[str, Any]) -> bool:
        raise NotImplementedError

    @abstractmethod
    def cancel_booking(self, *, booking_id: str) -> bool:
        raise NotImplementedError
