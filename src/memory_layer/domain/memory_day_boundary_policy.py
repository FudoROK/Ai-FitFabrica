from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MemoryDayBoundary:
    """Resolved memory-day boundary for a single event timestamp."""

    memory_day_key: str
    memory_day_start_utc: datetime
    memory_day_end_utc: datetime
    memory_day_start_local: datetime
    memory_day_end_local: datetime


class MemoryDayBoundaryPolicy:
    """Domain policy for memory-day boundaries.

    Semantics:
    - memory-day starts at local cutoff time (cutoff_hour:cutoff_minute).
    - if event local time is before cutoff, event belongs to the previous memory-day.
    """

    @staticmethod
    def resolve_for_event(
        *,
        occurred_at_utc: datetime,
        timezone_name: str,
        cutoff_hour: int,
        cutoff_minute: int,
    ) -> MemoryDayBoundary:
        tz = ZoneInfo(timezone_name)
        occurred_local = occurred_at_utc.astimezone(tz)
        cutoff_local = occurred_local.replace(
            hour=cutoff_hour,
            minute=cutoff_minute,
            second=0,
            microsecond=0,
        )

        if occurred_local < cutoff_local:
            memory_day_start_local = cutoff_local - timedelta(days=1)
        else:
            memory_day_start_local = cutoff_local

        next_day_start_local = memory_day_start_local + timedelta(days=1)
        memory_day_end_local = next_day_start_local - timedelta(microseconds=1)

        return MemoryDayBoundary(
            memory_day_key=memory_day_start_local.strftime("%Y-%m-%d"),
            memory_day_start_utc=memory_day_start_local.astimezone(timezone.utc),
            memory_day_end_utc=memory_day_end_local.astimezone(timezone.utc),
            memory_day_start_local=memory_day_start_local,
            memory_day_end_local=memory_day_end_local,
        )

    @staticmethod
    def resolve_for_memory_day_key(
        *,
        memory_day_key: str,
        timezone_name: str,
        cutoff_hour: int,
        cutoff_minute: int,
    ) -> MemoryDayBoundary:
        tz = ZoneInfo(timezone_name)
        memory_day_start_local = datetime.strptime(memory_day_key, "%Y-%m-%d").replace(
            tzinfo=tz,
            hour=cutoff_hour,
            minute=cutoff_minute,
            second=0,
            microsecond=0,
        )
        next_day_start_local = memory_day_start_local + timedelta(days=1)
        memory_day_end_local = next_day_start_local - timedelta(microseconds=1)

        return MemoryDayBoundary(
            memory_day_key=memory_day_key,
            memory_day_start_utc=memory_day_start_local.astimezone(timezone.utc),
            memory_day_end_utc=memory_day_end_local.astimezone(timezone.utc),
            memory_day_start_local=memory_day_start_local,
            memory_day_end_local=memory_day_end_local,
        )
