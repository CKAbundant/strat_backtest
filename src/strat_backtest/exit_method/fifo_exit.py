"""Implementation of FIFOExit class

- Concrete implementation of 'ExitStruct' abstract class
- Reduce position via first-in-first-out.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from strat_backtest.base import ExitStruct
from strat_backtest.utils import ClosedPositionResult, OpenTrades

if TYPE_CHECKING:
    from strat_backtest.utils import CompletedTrades


class FIFOExit(ExitStruct):
    """Take profit for earliest open trade. For example:

    - Long stock at 50 (5 lots) -> 60 (3 lots) -> 70 2 lots).
    - Signal to take profit -> Sell 5 lots bought at 50 (i.e. FIFO).
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

        completed_trades = []
        earliest_trade = open_trades[0]

        # Update earliest StockTrade object
        earliest_trade = self._update_pos(earliest_trade, dt, exit_price)

        # Convert StockTrade to dictionary only if all fields are populated
        # i.e. trade completed.
        if self._validate_completed_trades(earliest_trade):
            # Remove earliest StockTrade object since it is completed
            open_trades.popleft()

            completed_trades.append(earliest_trade.model_dump())

        return open_trades, completed_trades
