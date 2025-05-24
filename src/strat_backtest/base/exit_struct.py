"""Abstract class used to generate various exit stuctures."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import ValidationError

from strat_backtest.utils.constants import ClosedPositionResult, OpenTrades

if TYPE_CHECKING:
    from strat_backtest.utils import CompletedTrades

    from .stock_trade import StockTrade


class ExitStruct(ABC):
    """Abstract class to populate 'StockTrade' pydantic object to close
    existing open positions fully or partially.

    - Exit open position with either profit or loss.
    - Incorporates fixed percentage gain and percentage loss.

    Args:
        None.

    Attributes:
        None.
    """

    @abstractmethod
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

        ...

    def _update_pos(
        self,
        trade: "StockTrade",
        dt: datetime,
        exit_price: float,
        exit_lots: int | None = None,
    ) -> "StockTrade":
        """Update existing StockTrade objects (still open).

        Args:
            trade (StockTrade):
                Existing StockTrade object for open trade.
            dt (datetime):
                Trade datetime object.
            exit_price (float):
                Exit price of stock ticker.
            exit_lots (int | None):
                If provided, number of lot to exit open position.

        Returns:
            (StockTrade): StockTrade object updated with exit info
        """

        # set exit_lots to be net entry and exit lots to ensure
        exit_lots = exit_lots or trade.entry_lots

        # Get exit action to update position
        exit_action = "sell" if trade.entry_action == "buy" else "buy"
        updated_trade = trade.model_copy()

        try:
            updated_trade.exit_datetime = dt
            updated_trade.exit_action = exit_action
            updated_trade.exit_lots = exit_lots
            updated_trade.exit_price = Decimal(str(exit_price))

            return updated_trade

        except ValidationError as e:
            print(f"Validation Error : {e}")
            return trade

    def _validate_completed_trades(self, stock_trade: "StockTrade") -> bool:
        """Validate whether StockTrade object is properly updated with no null
        values."""

        # Check for null fields
        is_no_null_field = all(
            field is not None for field in stock_trade.model_dump().values()
        )

        # Check if number of entry lots must equal number of exit lots
        is_lots_matched = stock_trade.entry_lots == stock_trade.exit_lots

        return is_no_null_field and is_lots_matched
