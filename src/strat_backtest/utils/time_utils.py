"""Utility functions to handle datetime objects."""

import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def convert_tz(dt: datetime, tz: str) -> datetime:
    """Convert to timezone aware."""

    try:
        # Check if tz is a valid timezone location
        time_zone = ZoneInfo(tz)

        if dt.tzinfo is None:
            # Convert naive datetime to time-zone aware
            dt = dt.replace(tzinfo=time_zone)
        else:
            # Amend time for time-aware datetime to desired timezone
            dt = dt.astimezone(tz=time_zone)

        return dt

    except ZoneInfoNotFoundError as e:
        raise ZoneInfoNotFoundError(f"'{tz}' is not a valid timezone string : {e}")

    except IsADirectoryError as e:
        raise IsADirectoryError(f"'{tz}' is a directory : {e}")

    except ValueError as e:
        raise ValueError(f"'{tz}' is incomplete relative path : {e}")


def list_valid_tz(keyword: str | None = None) -> None:
    """List all valid timezone that contains keyword.

    Args:
        keyword (str | None):
            If provided, keyword that is found in time zone string.
            If None, return all valid timezones.

    Returns:
        None.
    """

    avail_tz = zoneinfo.available_timezones()

    if keyword:
        required_tz = [tz for tz in avail_tz if keyword in tz]
        msg = f"Timezones containing '{keyword}'"

    tz_list = required_tz if keyword else sorted(list(avail_tz))
    msg = f"Timezones containing '{keyword}'" if keyword else "All Timezones"

    print(f"\n\n{msg} :\n")

    for count, tz in enumerate(tz_list, start=1):
        print(f"{count:>3}. {tz}")


__all__ = [
    "convert_tz",
    "list_valid_tz",
]
