"""A timestamp factory that advances only when explicitly stepped."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


class DeterministicClock:
    """Useful for deterministic audit timestamps."""

    def __init__(self, start: datetime | None = None) -> None:
        self._now = start if start is not None else datetime(2024, 1, 1, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self._now

    def advance(self, interval: timedelta) -> None:
        if interval < timedelta(0):
            raise ValueError("Interval must not be negative.")
        self._now += interval
