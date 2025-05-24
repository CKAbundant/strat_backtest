"""Implementation of HalfLIFOExit class

- Concrete implementation of 'ExitStruct' abstract class
- Reduce positions by half each time via last-in-first-out.
"""

from datetime import datetime

from strat_backtest.base import HalfExitStruct
from strat_backtest.utils.constants import (
    ClosedPositionResult,
    CompletedTrades,
    OpenTrades,
)


class HalfLIFOExit(HalfExitStruct):
    """keep taking profit by exiting half of latest positions . For example:

    - Long stock at 50 (5 lots) -> 60 (3 lots) -> 70 (2 lots).
    - Signal to take profit -> Sell 2 lots bought at 70 and 3 lots bought at 60
    i.e. left 50 (5 lots)
    - Signal to take profit again -> sell 3 lots bought at 50
    i.e. left 50 (2 lots).
    """

    def close_pos(
        self,
        open_trades: OpenTrades,
        dt: datetime,
        exit_price: float,
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

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' objects.
            completed_trades (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        if len(open_trades) == 0:
            # No open trades to close
            return open_trades, []

        # Reverse copy of 'open_trades'
        open_trades_copy = open_trades.copy()
        open_trades_list = list(open_trades_copy)
        reversed_open_trades = tuple(open_trades_list[::-1])

        new_open_trades, completed_trades = self._update_half_status(
            reversed_open_trades, dt, exit_price
        )

        return new_open_trades, completed_trades
