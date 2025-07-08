"""Trading system constants and enumerations.

This module contains StrEnum classes and Literal type constants
used throughout the 'strat_backtest' package.
"""

import sys
from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, TypeAlias

if TYPE_CHECKING:
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
ExitType = Literal["stop", "trail"]


# Dynamic variables
class EntryMethod(StrEnum):
    MULTIPLE = "MultiEntry"
    MULTIPLE_HALF = "MultiHalfEntry"
    SINGLE = "SingleEntry"


class ExitMethod(StrEnum):
    FIFO = "FIFOExit"
    LIFO = "LIFOExit"
    HALF_FIFO = "HalfFIFOExit"
    HALF_LIFO = "HalfLIFOExit"
    TAKE_ALL = "TakeAllExit"


class SigEvalMethod(StrEnum):
    BREAKOUT_ENTRY = "BreakoutEntry"
    CLOSE_ENTRY = "CloseEntry"


class TrailMethod(StrEnum):
    NO_TRAIL = "no_trail"
    FIRST_TRAIL = "FirstTrail"
    LATEST_TRAIL = "LastestTrail"
    MEAN_TRAIL = "MeanTrail"


class StopMethod(StrEnum):
    NO_STOP = "no_stop"
    PERCENT_LOSS = "PercentLoss"
    LATEST_LOSS = "LatestLoss"
    NEAREST_LOSS = "NearestLoss"


# Type aliases for trading system
OpenTrades: TypeAlias = deque["StockTrade"]
CompletedTrades: TypeAlias = list[dict[str, Decimal | str | datetime]]
ClosedPositionResult: TypeAlias = tuple[OpenTrades, CompletedTrades]
Record: TypeAlias = dict[str, PriceAction | Decimal | datetime]

# Public interface
__all__ = [
    "PriceAction",
    "EntryType",
    "ExitType",
    "SigEvalMethod",
    "EntryMethod",
    "ExitMethod",
    "StopMethod",
    "OpenTrades",
    "CompletedTrades",
    "ClosedPositionResult",
    "Record",
]
