"""Trading system constants and enumerations.

This module contains StrEnum classes and Literal type constants
used throughout the 'strat_backtest' package.
"""

import sys
from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, TypeAlias

from strat_backtest.base.stock_trade import StockTrade

if sys.version_info >= (3, 11):
    # pylint: disable=wrong-import-position
    from enum import StrEnum
else:
    from enum import Enum

    # Fallback for Python < 3.11
    class StrEnum(str, Enum):
        """String enumeration for Python < 3.11 compatibility."""

        ...


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


# Type aliases for trading system
OpenTrades: TypeAlias = deque[StockTrade]
CompletedTrades: TypeAlias = list[dict[str, Decimal | str | datetime]]
ClosedPositionResult: TypeAlias = tuple[OpenTrades, CompletedTrades]

# Public interface
__all__ = [
    "PriceAction",
    "EntryType",
    "EntryMethod",
    "ExitMethod",
    "StopMethod",
    "OpenTrades",
    "CompletedTrades",
    "ClosedPositionResult",
]
