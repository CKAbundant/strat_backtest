"""Implementation of SingleEntry class

- Concrete implementation of 'EntryStruct' abstract class
- Allows only a single open position at any time.
- Meaning no new position can be initiated unless existing position is closed.
"""

from datetime import datetime

from strat_backtest.base import EntryStruct
from strat_backtest.utils.constants import OpenTrades, PriceAction


class SingleEntry(EntryStruct):
    """Allows only 1 position of same ticker i.e. no new open position created
    if there is existing open position.

    - Number of lots entered are fixed to 'self.num_lots'.

    Usage:
        >>> open_trades = deque()
        >>> ticker = "AAPL"
        >>> dt = datetime(2025, 4, 11)
        >>> entry_price = 200.0
        >>> entry_signal = "buy"
        >>> single_entry = SingleEntry(num_lots=1)
        >>> open_trades = single_entry.open_new_pos(
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
            entry_signal (PriceAction):
                Entry signal i.e. "buy", "sell" or "wait" to create new position.
            entry_price (float):
                Entry price for stock ticker.

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' objects.
        """

        if len(open_trades) > 0:
            # No new position added since there is existing position
            return open_trades

        # Create StockTrade object to record new long/short position
        # based on 'entry_signal'
        if stock_trade := self._create_new(
            open_trades, ticker, dt, entry_signal, entry_price
        ):
            open_trades.append(stock_trade)
            self._validate_open_trades(open_trades)

        return open_trades
