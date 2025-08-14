"""Implementation of MultiEntry class

- Concrete implementation of 'EntryStruct' abstract class
- Allows multiple positions for same ticker.
"""

from datetime import datetime

from strat_backtest.base import EntryStruct
from strat_backtest.utils.constants import OpenTrades, PriceAction


class MultiEntry(EntryStruct):
    """Allows multiple positions of same ticker i.e. new 'StockTrade' pydantic
    objects with same entry lots.

    - Add new long/short positions even if existing long/short positions.
    - Number of lots entered are fixed to 'self.num_lots'.There

    Usage:
        >>> open_trades = deque()
        >>> ticker = "AAPL"
        >>> dt = datetime(2025, 4, 11)
        >>> entry_price = 200.0
        >>> entry_signal = "buy"
        >>> multi_entry = MultiEntry(num_lots=1)
        >>> open_trades = multi_entry.open_new_pos(
                open_trades, ticker, dt, entry_price, entry_signal
            )
    """

    def open_new_pos(
        self,
        open_trades: OpenTrades,
        ticker: str,
        dt: datetime | str,
        entry_signal: PriceAction,
        entry_price: float,
    ) -> OpenTrades:
        """Generate new 'StockTrade' object populating 'ticker', 'entry_date',
        'entry_lots' and 'entry_price'.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade pydantic object to record open trades.
            ticker (str):
                Stock ticker to be traded.
            dt (datetime | str):
                Trade datetime object or string in "YYYY-MM-DD" format.
            entry_signal (PriceAction):
                Entry signal i.e. "buy", "sell" or "wait" to create new position.
            entry_price (float):
                Entry price for stock ticker.

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' objects.
        """

        # Create StockTrade object to record new long/short position
        # based on 'entry_signal'
        if not (
            stock_trade := self._create_new(
                open_trades, ticker, dt, entry_signal, entry_price
            )
        ):
            return open_trades

        open_trades.append(stock_trade)
        self._validate_open_trades(open_trades)

        return open_trades
