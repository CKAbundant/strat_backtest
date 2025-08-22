"""Implementation of HalfFIFOExit class

- Concrete implementation of 'ExitStruct' abstract class
- Reduce positions by half each time via first-in-first-out.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from strat_backtest.base import HalfExitStruct
from strat_backtest.utils.constants import ClosedPositionResult, OpenTrades

if TYPE_CHECKING:
    from strat_backtest.base.stock_trade import StockTrade
    from strat_backtest.utils.constants import CompletedTrades


class HalfFIFOExit(HalfExitStruct):
    """keep taking profit by exiting half of earliest positions. For example:

    - Long stock at 50 (5 lots) -> 60 (3 lots) -> 70 (2 lots).
    - Signal to take profit -> Sell 5 lots (50% of total 10 lots) bought at 50
    i.e. left 60 (3 lots), 70 (2 lots)
    - Signal to take profit again -> sell 3 lots (50% of total 5 lots) bought at 60
    i.e. left 70 (2 lots).
    """

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
            # No open trades to close
            return open_trades, []

        new_open_trades, completed_trades = self._update_half_status(
            open_trades.copy(), dt, exit_price
        )

        return new_open_trades, completed_trades
