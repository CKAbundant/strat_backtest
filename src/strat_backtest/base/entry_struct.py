"""Abstract class used to generate various entry stuctures."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from pydantic import ValidationError

from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.utils.constants import OpenTrades, PriceAction
from strat_backtest.utils.pos_utils import get_std_field


class EntryStruct(ABC):
    """Abstract class to populate 'StockTrade' pydantic object to record
    open trades.

    Args:
        num_lots (int):
            Default number of lots to enter each time (Default: 1).

    Attributes:
        num_lots (int):
            Default number of lots to enter each time (Default: 1).
    """

    def __init__(self, num_lots: int) -> None:
        self.num_lots = num_lots

    @abstractmethod
    def open_new_pos(
        self,
        open_trades: OpenTrades,
        ticker: str,
        dt: datetime | str,
        ent_sig: PriceAction,
        entry_price: float,
    ) -> OpenTrades:
        """Generate new 'StockTrade' object populating 'ticker', 'entry_date',
        'entry_lots' and 'entry_price'.

        Args:
            open_trades (deque[StockTrade]):
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
            open_trades (deque[StockTrade]):
                Updated deque list of 'StockTrade' objects.
        """

        ...

    def _create_new(
        self,
        open_trades: OpenTrades,
        ticker: str,
        dt: datetime | str,
        ent_sig: PriceAction,
        entry_price: float,
        entry_lots: int | None = None,
    ) -> "StockTrade" | None:
        """Generate new 'StockTrade' object populating 'ticker', 'entry_date',
        'entry_lots' and 'entry_price'.

        Args:
            open_trades (deque[StockTrade]):
                Deque list of StockTrade pydantic object to record open trades.
            ticker (str):
                Stock ticker to be traded.
            dt (datetime | str):
                Trade datetime object or string in "YYYY-MM-DD" format.
            ent_sig (PriceAction):
                Entry signal i.e. "buy", "sell" or "wait" to create new position.
            entry_price (float):
                Entry price for stock ticker.
            entry_lots (int | None):
                If provided, entry lots to enter for 'MultiHalfEntry' entry structure.

        Returns:
            (StockTrade | None): If available, newly created StockTrade object.
        """

        entry_lots = entry_lots or self.num_lots

        try:
            return StockTrade(
                ticker=self._validate_ticker(open_trades, ticker),
                entry_datetime=self._validate_entry_datetime(open_trades, dt),
                entry_action=self._validate_entry_action(open_trades, ent_sig),
                entry_lots=Decimal(str(entry_lots)),
                entry_price=Decimal(str(entry_price)),
            )

        except ValidationError as e:
            print(f"Validation Error: {e}")
            return None

    def _validate_ticker(self, open_trades: OpenTrades, ticker: str) -> str:
        """Validate ticker is the same for all StockTrade objects in 'open_trades.

        Args:
            open_trades (OpenTrades):
                Deque collection of open trades.
            ticker (str):
                Stock ticker used to create new open trade.

        Return:
            ticker (str):
                Validated stock ticker used to create new open trade.
        """

        if len(open_trades) == 0:
            return ticker

        # Check if ticker used is the same as latest ticker in 'open_trades'
        latest_ticker = open_trades[-1].ticker
        if ticker != latest_ticker:
            raise ValueError(
                f"'{ticker}' is different from ticker used in "
                f"'open_trades' ({latest_ticker})"
            )

        return ticker

    def _validate_entry_action(
        self, open_trades: OpenTrades, entry_action: PriceAction
    ) -> PriceAction:
        """Validate entry action is the same for all StockTrade objects in 'open_trades.

        Args:
            open_trades (OpenTrades):
                Deque collection of open trades.
            entry_action (PriceAction):
                Entry action used to create new open trade.

        Return:
            entry_action (PriceAction):
                Entry action used to create new open trade.
        """

        if len(open_trades) == 0:
            return entry_action

        # Check if 'entry_action' is the same used latest entry in 'open_trades'
        latest_action = open_trades[-1].entry_action
        if entry_action != latest_action:
            raise ValueError(
                f"'{entry_action}' is different from entry action used in"
                f"'open_trades' ({latest_action})"
            )

        return entry_action

    def _validate_entry_datetime(
        self, open_trades: OpenTrades, entry_datetime: datetime | str
    ) -> datetime:
        """Validate entry datetime is the same for all StockTrade objects
        in 'open_trades.

        Args:
            open_trades (OpenTrades):
                Deque collection of open trades.
            entry_datetime (datetime | str):
                Entry datetime used to create new open trade
                ("YYYY-MM-DD_HHMM" or "YYYY-MM-DD" if string).

        Return:
            entry_datetime (datetime):
                Validated entry datetime used to create new open trade.
        """

        if isinstance(entry_datetime, str):
            if "_" in entry_datetime:
                # YYYY-MM-HH_HHMM format
                entry_datetime = datetime.strptime(entry_datetime, "%Y-%m-%d_%H%M")
            else:
                # YYYY-MM-HH format
                entry_datetime = datetime.strptime(entry_datetime, "%Y-%m-%d")

        if len(open_trades) == 0:
            return entry_datetime

        # Check if entry datetime is less than latest entry datetime in 'open_trades'
        latest_datetime = open_trades[-1].entry_datetime
        if entry_datetime < latest_datetime:
            raise ValueError(
                f"Entry datetime '{entry_datetime}' is earlier than "
                f"latest entry datetime '{latest_datetime}'."
            )

        return entry_datetime

    def _validate_open_trades(self, open_trades: OpenTrades) -> None:
        """Validate StockTrade objects in 'self.open_trade'.

        -'entry_action' fields are  same for all StockTrade objects.
        - 'ticker' fields are same for all StockTrade objects.
        - 'entry_date' should be later than the latest StockTrade object
        in 'open_trades'.
        """

        if len(open_trades) == 0:
            raise ValueError(
                "'open_trades' is still empty after creating new position."
            )

        # Validate 'ticker' and 'entry_action' fields are consistent
        get_std_field(open_trades, "ticker")
        get_std_field(open_trades, "entry_action")

        # Validate all entry_datetime are in ascending order
        entry_dates = [trade.entry_datetime for trade in open_trades]
        if any(
            entry_dates[idx] > entry_dates[idx + 1]
            for idx in range(len(entry_dates) - 1)
        ):
            raise ValueError(
                "'entry_date' field is not sequential i.e. entry_date is lower than "
                "the entry_date in the previous item."
            )

        # Validate all exit lots are less than entry lots
        if any(trade.exit_lots >= trade.entry_lots for trade in open_trades):
            raise ValueError("Completed trades observed in 'open_trades'.")
