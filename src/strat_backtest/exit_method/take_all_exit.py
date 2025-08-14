"""Implementation of TakeAllExit class

- Concrete implementation of 'ExitStruct' abstract class
- Exit all open positions if triggered.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from strat_backtest.base import ExitStruct
from strat_backtest.utils.constants import ClosedPositionResult, OpenTrades
from strat_backtest.utils.pos_utils import (
    gen_completed_trade,
    validate_completed_trades,
)

if TYPE_CHECKING:
    from strat_backtest.base.stock_trade import StockTrade
    from strat_backtest.utils.constants import CompletedTrades


class TakeAllExit(ExitStruct):
    """Exit all open positions at a loss."""

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

        completed_trades = []

        for trade in open_trades:
            initial_exit_lots = trade.exit_lots

            # Update to close open position
            trade = self._update_pos(trade, dt, exit_price)

            # Break loop if trade is not updated properly i.e.
            # trade.exit_lots = initial_exit_lots
            if trade.exit_lots == initial_exit_lots:
                # Return original 'open_trades' and empty completed trades list
                # if trade is None i.e. ValidationError
                return open_trades, []

            if initial_exit_lots > 0:
                # Number of lots to close partial open position
                lots_to_exit = trade.entry_lots - initial_exit_lots

                # Create completed trades using 'lots_to_exit'
                completed_trades.append(gen_completed_trade(trade, lots_to_exit))

            else:
                # Generate completed trades for fully open position
                if validate_completed_trades(trade):
                    completed_trades.append(trade.model_dump())

        if len(completed_trades) != len(open_trades):
            raise ValueError("Open positions failed to close completely.")

        # Reset open_trades
        open_trades.clear()

        return open_trades, completed_trades
