from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class WindowCloseTiming:
    """Unified active-window close timing computed by domain policy."""

    grace_until_utc: datetime
    close_threshold_utc: datetime
    window_close_at_utc: datetime


class WindowClosePolicy:
    """Domain policy for active-window close timing.

    Inputs:
    - opened_at: UTC timestamp when the window started.
    - last_activity_at: UTC timestamp of the last observed activity.
      Kept for backward compatibility; not used in cutoff-based close semantics.
    - timezone_name: IANA timezone for local cutoff calculation.
    - cutoff_hour/cutoff_minute: local-day close time.
    - grace_period: retained for interface compatibility.
    """

    @staticmethod
    def resolve(
        *,
        opened_at: datetime,
        last_activity_at: datetime,
        timezone_name: str,
        cutoff_hour: int,
        cutoff_minute: int,
        grace_period: timedelta,
    ) -> WindowCloseTiming:
        _ = (last_activity_at, grace_period)
        tz = ZoneInfo(timezone_name)
        opened_local = opened_at.astimezone(tz)

        cutoff_local = opened_local.replace(
            hour=cutoff_hour,
            minute=cutoff_minute,
            second=0,
            microsecond=0,
        )
        if opened_local >= cutoff_local:
            cutoff_local = cutoff_local + timedelta(days=1)

        window_close_at_utc = cutoff_local.astimezone(opened_at.tzinfo)
        grace_until_utc = window_close_at_utc
        close_threshold_utc = window_close_at_utc

        return WindowCloseTiming(
            grace_until_utc=grace_until_utc,
            close_threshold_utc=close_threshold_utc,
            window_close_at_utc=window_close_at_utc,
        )
