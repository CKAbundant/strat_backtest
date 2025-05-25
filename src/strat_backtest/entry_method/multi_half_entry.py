"""Implementation of MultiHalfEntry class

- Concrete implementation of 'EntryStruct' abstract class
- Allows multiple positions for same ticker.
- Number of new open positions are half of the previous quantity to
reduce risk.
"""

import math
from datetime import datetime
from decimal import Decimal

from strat_backtest.base import EntryStruct
from strat_backtest.utils.constants import OpenTrades, PriceAction


class MultiHalfEntry(EntryStruct):
    """Allows multiple positions of same ticker i.e. new 'StockTrade' pydantic
    objects with entry lots decreasing by half with each multiple entry.

    - Add new long/short positions even if existing long/short positions.
    - Number of lots entered decreases from 'self.num_lots' by half e.g.
    10 -> 5 -> 2 -> 1
    - Only if 'self.num_lots' > 1; and no fractional lots allowed.

    Usage:
        >>> open_trades = deque()
        >>> ticker = "AAPL"
        >>> dt = datetime(2025, 4, 11)
        >>> entry_price = 200.0
        >>> ent_sig = "buy"
        >>> multi_entry = MultiHalfEntry(num_lots=1)
        >>> open_trades = multi_entry.open_new_pos(
                open_trades, ticker, dt, entry_price, ent_sig
            )
    """

    def open_new_pos(
        self,
        open_trades: OpenTrades,
        ticker: str,
        dt: datetime | str,
        ent_sig: PriceAction,
        entry_price: float,
    ):
        """Generate new 'StockTrade' object populating 'ticker', 'entry_date',
        'entry_lots' and 'entry_price'.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade pydantic object to record open trades.
            ticker (str):
                Stock ticker to be traded.
            dt (datetime | str):
                Trade datetime object or string in "YYYY-MM-DD" format.
            ent_sig (PriceAction):
                Entry signal i.e. "buy", "sell" or "wait" to create new position.
            entry_price (float):
                Entry price for stock ticker.

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' objects.
        """

        # Get number of lots to enter for new position
        entry_lots = self.get_half_lots(open_trades)

        # Create StockTrade object to record new long/short position
        # based on 'ent_sig'
        if stock_trade := self._create_new(
            open_trades, ticker, dt, ent_sig, entry_price, entry_lots
        ):
            open_trades.append(stock_trade)
            self._validate_open_trades(open_trades)

        return open_trades

    def get_half_lots(self, open_trades: OpenTrades) -> Decimal:
        """Get half of latest StockTrade object in 'open_trades' till
        minimum 1 lot."""

        return (
            math.ceil((open_trades[-1].entry_lots - open_trades[-1].exit_lots) / 2)
            if len(open_trades) > 0
            else self.num_lots
        )
