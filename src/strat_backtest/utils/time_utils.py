"""Utility functions to handle datetime objects."""

import re
import zoneinfo
from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pandas as pd


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
        raise ZoneInfoNotFoundError(
            f"'{tz}' is not a valid timezone string : {e}"
        ) from e

    except IsADirectoryError as e:
        raise IsADirectoryError(f"'{tz}' is a directory : {e}") from e

    except ValueError as e:
        raise ValueError(f"'{tz}' is incomplete relative path : {e}") from e


def convert_to_datetime(var: Any, dayfirst: bool = False) -> datetime | Any:
    """Convert variable to pd.Timestamp before converting to datetime type
    if it can be converted to datetime object else return the variable unchanged.

    Args:
        var (Any): Variable of any data type.
        dayfirst (bool): Whether string format is day first (Default: False).

    Returns:
        (datetime | Any): variable of datetime type or original data type.
    """

    if isinstance(var, (int, float, Decimal)):
        # No conversion to datetime if numeric type
        return var

    if isinstance(var, str):
        dayfirst = validate_dayfirst(var, dayfirst)

    dt_var = pd.to_datetime(var, errors="coerce", dayfirst=dayfirst)

    if pd.isnull(dt_var):
        # variable is set to 'NaT' data type
        return var

    return dt_var.to_pydatetime()


def validate_dayfirst(var: str, user_dayfirst: bool) -> bool:
    """Validate if the variable string is of dayfirst format else
    follow user specified dayfirst setting.

    - "30-10-2025" -> dayfirst=True
    - "10/20/2025 -> dayfirst=False
    """

    # Split string by '/' or '-'
    num_list = re.split(r"[/-]", var)

    print(f"\n{var=}")
    print(f"{num_list=}")

    if len(num_list) != 3:
        return user_dayfirst

    try:
        # Convert items in list to integers
        num_list = [int(item) for item in num_list]

        if any(num <= 0 or num > 31 for num in num_list[:1]) or (
            num_list[0] > 12 and num_list[1] > 12
        ):
            # Ensure first 2 numbers are not negative or more than 31
            return user_dayfirst

        if num_list[0] > 12:
            # first number is more than 12. Hence cannot represent month
            return True

        if num_list[1] > 12:
            # Second number is more than 12. Hence cannot represent month
            return False

        return user_dayfirst

    except TypeError:
        # Contains letters hence cannot be converted to numbers
        return user_dayfirst


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
    required_tz = []

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
    "convert_to_datetime",
]
