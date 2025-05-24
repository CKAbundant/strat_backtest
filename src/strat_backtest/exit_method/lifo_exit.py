"""Implementation of LIFOExit class

- Concrete implementation of 'ExitStruct' abstract class
- Reduce position via last-in-first-out.
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from strat_backtest.base import ExitStruct
from strat_backtest.utils import ClosedPositionResult, OpenTrades

if TYPE_CHECKING:
    from strat_backtest.utils import CompletedTrades


class LIFOExit(ExitStruct):
    """Take profit for latest open trade. For example:

    - Long stock at 50 (5 lots) -> 60 (3 lots) -> 70 (2 lots).
    - Signal to take profit -> Sell 2 lots bought at 70 (i.e. FIFO).
    """

    def close_pos(
        self,
        open_trades: OpenTrades,
        dt: datetime,
        exit_price: Decimal,
    ) -> ClosedPositionResult:
        """Update existing StockTrade objects (still open); and remove completed
        StockTrade objects in 'open_trades'.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade pydantic object to record open trades.
            dt (datetime):
                Trade datetime object.
            exit_price (Decimal):
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
        latest_trades = open_trades[-1]

        # Update earliest StockTrade object
        latest_trades = self._update_pos(latest_trades, dt, exit_price)

        # Convert StockTrade to dictionary only if all fields are populated
        # i.e. trade completed.
        if self._validate_completed_trades(latest_trades):
            # Remove latest StockTrade object from 'open_trades'
            open_trades.pop()

            completed_trades.append(latest_trades.model_dump())

        return open_trades, completed_trades
