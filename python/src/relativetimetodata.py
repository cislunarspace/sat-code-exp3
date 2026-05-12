from __future__ import annotations

from datetime import datetime, timedelta

DAY_SECONDS = 86_400


def seconds_to_datetime(relative_seconds: float, base_time: datetime) -> datetime:
    base_day = base_time.replace(hour=0, minute=0, second=0, microsecond=0)
    return base_day + timedelta(seconds=relative_seconds)


def relativetimetodata(relative_times: list[float], base_time: datetime) -> list[datetime]:
    return [seconds_to_datetime(relative_time, base_time) for relative_time in relative_times]
