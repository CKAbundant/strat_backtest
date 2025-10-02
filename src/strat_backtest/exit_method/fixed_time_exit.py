"""Implementation of FixedTimeExit class

- Concrete implementation of 'ExitStruct' abstract class
- Closes positions after a fixed time period (number of trading days/bars)
"""

from datetime import datetime
from typing import TYPE_CHECKING

from strat_backtest.base import ExitStruct
from strat_backtest.utils.constants import ClosedPositionResult, OpenTrades
from strat_backtest.utils.pos_utils import validate_completed_trades

if TYPE_CHECKING:
    from strat_backtest.utils.constants import CompletedTrades


class FixedTimeExit(ExitStruct):
    """Exit positions after a fixed time period.

    Automatically closes open positions after a predetermined number of trading days
    have passed since the position was opened.

    Args:
        time_period (int):
            Number of trading days to hold position before automatic exit
            (Default: 5).

    Attributes:
        time_period (int):
            Number of trading days to hold position before automatic exit.
    """

    def __init__(self, time_period: int = 5) -> None:
        if time_period <= 0:
            raise ValueError("time_period must be a positive integer")
        self.time_period = time_period

    def close_pos(
        self,
        open_trades: OpenTrades,
        dt: datetime,
        exit_price: float,
        _entry_dt: datetime | None = None,
    ) -> ClosedPositionResult:
        """Update existing StockTrade objects (still open); and remove completed
        StockTrade objects in 'open_trades'.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade pydantic object to record open trades.
            dt (datetime):
                Trade datetime object.
            exit_price (float):
                Exit price of stock ticker.
            _entry_dt (datetime | None):
                If provided, datetime when position is opened.

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' objects.
            completed_trades (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """
        if len(open_trades) == 0:
            return open_trades, []

        completed_trades = []

        # Use list comprehension to find positions to close
        positions_to_close = [
            trade
            for trade in open_trades
            if (dt - trade.entry_datetime).days >= self.time_period
        ]

        # Single loop to close positions
        for trade in positions_to_close:
            updated_trade = self._update_pos(trade, dt, exit_price)

            if validate_completed_trades(updated_trade):
                open_trades.remove(trade)
                completed_trades.append(updated_trade.model_dump())

        return open_trades, completed_trades
