"""Trading system constants and enumerations.

This module contains StrEnum classes and Literal type constants
used throughout the 'pos_mgmt' package.
"""

import sys

if sys.version_info >= (3, 11):
    # pylint: disable=wrong-import-position
    from enum import StrEnum
else:
    from enum import Enum

    # Fallback for Python < 3.11
    class StrEnum(str, Enum):
        """String enumeration for Python < 3.11 compatibility."""

        ...


from enum import StrEnum
from typing import Literal

# Static variables
PriceAction = Literal["buy", "sell", "wait"]
EntryType = Literal["long", "short", "longshort"]


# Dynamic variables
class EntryMethod(StrEnum):
    MULTIPLE = "multiple"
    MULTIPLE_HALF = "multiple_half"
    SINGLE = "single"


class ExitMethod(StrEnum):
    FIFO = "fifo"
    LIFO = "lifo"
    HALF_FIFO = "half_fifo"
    HALF_LIFO = "half_lifo"
    TAKE_ALL = "take_all"


class StopMethod(StrEnum):
    NO_STOP = "no_stop"
    PERCENT_LOSS = "percent_loss"
    LATEST_LOSS = "latest_loss"
    NEAREST_LOSS = "nearest_loss"


# Public interface
__all__ = [
    "PriceAction",
    "EntryType",
    "EntryMethod",
    "ExitMethod",
    "StopMethod",
]
