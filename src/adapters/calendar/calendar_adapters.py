from __future__ import annotations

from typing import Any, Optional

from src.domain.contracts.calendar import CalendarContract


class NoCalendarAdapter(CalendarContract):
    def list_events(self, *, start_iso: str, end_iso: str) -> list[dict[str, Any]]:
        return []

    def create_booking(self, *, payload: dict[str, Any]) -> Optional[str]:
        return None

    def reschedule_booking(self, *, booking_id: str, payload: dict[str, Any]) -> bool:
        return False

    def cancel_booking(self, *, booking_id: str) -> bool:
        return False
