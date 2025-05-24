"""Implementation of HalfLIFOExit class

- Concrete implementation of 'ExitStruct' abstract class
- Reduce positions by half each time via last-in-first-out.
"""

import math
from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from strat_backtest.base import ExitStruct
from strat_backtest.utils.constants import (
    ClosedPositionResult,
    CompletedTrades,
    OpenTrades,
)
from strat_backtest.utils.pos_utils import get_net_pos

if TYPE_CHECKING:
    from strat_backtest.base.stock_trade import StockTrade


class HalfLIFOExit(ExitStruct):
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

        completed_trades = []
        new_open_trades = deque()

        if len(open_trades) == 0:
            # No open trades to close
            return open_trades, []

        # Reverse copy of 'self.open_trades'
        open_trades_list = list(open_trades)
        reversed_open_trades = open_trades_list[::-1]

        # Get net position and half of net position from 'open_trades'
        net_pos = get_net_pos(open_trades)
        half_pos = math.ceil(abs(net_pos) / 2)

        for trade in reversed_open_trades:
            initial_exit_lots = trade.exit_lots

            # Update trade only if haven't reach half of net position
            if half_pos > 0:
                # Determine quantity to close based on 'half_pos'
                lots_to_exit = min(half_pos, trade.entry_lots - initial_exit_lots)

                # Update StockTrade objects with exit info
                trade = self._update_pos(
                    trade, dt, exit_price, initial_exit_lots + lots_to_exit
                )

                # Break loop if trade is not updated properly i.e.
                # trade.exit_lots = initial_exit_lots
                if trade.exit_lots == initial_exit_lots:
                    return open_trades, []

                # Only update 'new_open_trades' if trades are still partially closed
                if not self._validate_completed_trades(trade):
                    new_open_trades.append(trade)

                # Create completed trades using 'lots_to_exit'
                completed_trades.append(self._gen_completed_trade(trade, lots_to_exit))

                # Update remaining positions required to be closed and net position
                half_pos -= lots_to_exit

            # trade not updated
            else:
                new_open_trades.appendleft(trade)

        return new_open_trades, completed_trades

    def _gen_completed_trade(
        self, trade: "StockTrade", lots_to_exit: Decimal
    ) -> CompletedTrades:
        """Generate StockTrade object with completed trade from 'StockTrade'
        and convert to dictionary."""

        # Create a shallow copy of the updated trade
        completed_trade = trade.model_copy()

        # Update the 'entry_lots' and 'exit_lots' to be same as 'lots_to_exit'
        completed_trade.entry_lots = lots_to_exit
        completed_trade.exit_lots = lots_to_exit

        if not self._validate_completed_trades(completed_trade):
            raise ValueError("Completed trades not properly closed.")

        return completed_trade.model_dump()
