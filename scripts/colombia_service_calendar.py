"""Colombian GTFS service-day classification for Bucaramanga TPC.

Requires: pip install holidays
Times are local to America/Bogota. Holiday precedence overrides weekday.
"""
from __future__ import annotations

from datetime import date
from functools import lru_cache

import holidays


@lru_cache(maxsize=None)
def _colombian_holidays(year: int):
    return holidays.country_holidays("CO", years=[year])


def service_day_type(day: date) -> str:
    """Return 'sunday', 'saturday', or 'weekday' for a Colombian date."""
    if day in _colombian_holidays(day.year):
        return "sunday"
    if day.weekday() == 6:
        return "sunday"
    if day.weekday() == 5:
        return "saturday"
    return "weekday"


def frequency_period(day: date, local_time) -> str:
    """Return 'peak', 'offpeak', or 'sunday'.

    local_time must be a datetime.time representing America/Bogota wall time.
    Holiday and Sunday service always take precedence over peak windows.
    """
    day_type = service_day_type(day)
    if day_type == "sunday":
        return "sunday"
    if day_type == "saturday":
        return "offpeak"
    from datetime import time
    if time(7, 0) <= local_time < time(9, 0):
        return "peak"
    if time(17, 0) <= local_time < time(20, 0):
        return "peak"
    return "offpeak"
