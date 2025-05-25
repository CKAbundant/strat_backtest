"""Abstract class to compute trailing profit price for multiple open positions."""

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from strat_backtest.utils.constants import OpenTrades, PriceAction
from strat_backtest.utils.pos_utils import convert_to_decimal


class TrailProfit(ABC):
    """Abstract class to generate trailing profit price for multiple
    open positions based on price movement.

    Args:
        trigger_trail (Decimal):
            Percentage profit required to trigger trailing profit (Default: 0.2).
        step (float):
            If provided, percent profit increment to trail profit. If None,
            increment set to current high - trigger_trail_level.

    Attributes:
        trigger_trail (Decimal):
            Percentage profit required to trigger trailing profit (Default: 0.2).
        step (Decimal):
            If provided, percent price increment to trail profit. If None,
            price increment set to current high - trigger_trail_level.
        step_level (Decimal):
            Price increment to trail profit.
        ref_price:
            Reference price used to compute the trigger trail level.
        trigger_trail_level (Decimal):
            Minimum price level to trigger trailing profit.
        trailing_profit (Decimal):
            Trailing profit price level. If triggered, all open positions
            will be closed.
    """

    def __init__(self, trigger_trail: float = 0.2, step: float | None = None) -> None:
        self.trigger_trail = convert_to_decimal(trigger_trail)
        self.step = convert_to_decimal(step)
        self.step_level = None
        self.ref_price = None
        self.trigger_trail_level = None
        self.trailing_profit = None

    @abstractmethod
    def cal_trail_price(
        self, open_trades: OpenTrades, record: dict[str, Decimal | datetime]
    ) -> Decimal:
        """Calculate a single exit price for multiple open positions.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade containing open trades info.
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.

        Returns:
            (Decimal): Trailing profit price for all multiple open positions.
        """

        ...

    def _cal_trigger_trail_level(self, entry_action: PriceAction) -> Decimal:
        """Compute price level to activate trailing profit.

        Args:
            entry_action (PriceAction):
                Standard entry action for open positions.

        Returns:
            (Decimal):
                Trigger trail level for all multiple open positions i.e. minimum price
                to trigger trailing profit.
        """

        if self.ref_price is None:
            raise ValueError("'self.ref_price' is null value.")

        if not isinstance(self.ref_price, (int, float, Decimal)):
            raise TypeError("'self.ref_price' is not a valid numeric type.")

        # Ensure ref_price  is Decimal Type
        ref_price = convert_to_decimal(self.ref_price)

        return (
            ref_price * (1 + self.trigger_trail)
            if entry_action == "buy"
            else ref_price * (1 - self.trigger_trail)
        )

    def _cal_trailing_profit(
        self,
        record: dict[str, Decimal | datetime],
        entry_action: PriceAction,
    ) -> Decimal:
        """Calculate trailing profit based on current OHLC, reference price and
        entry action.

        Args:
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.
            entry_action (PriceAction):
                Standard entry action for open positions.

        Returns:
            (Decimal): Trailing profit price for all multiple open positions.
        """

        high = record["high"]
        low = record["low"]

        # Update trailing profit if current high must be higher than
        # trigger_trail_level for long positions
        if entry_action == "buy" and (excess := high - self.trigger_trail_level) >= 0:
            computed_trailing = (
                self.ref_price + excess
                if self.step_level is None
                else self.ref_price + (excess // self.step_level) * self.step_level
            )

            if self.trailing_profit is None or computed_trailing > self.trailing_profit:
                # Update trailing profit level if higher than previous level
                self.trailing_profit = computed_trailing

        # Update trailing profit if current low must be lower than
        # trigger_trail_level for short positions
        elif entry_action == "sell" and (excess := self.trigger_trail_level - low) >= 0:
            computed_trailing = (
                self.ref_price - excess
                if self.step_level is None
                else self.ref_price - (excess // self.step_level * self.step_level)
            )

            if self.trailing_profit is None or computed_trailing < self.trailing_profit:
                # Update trailing profit level if lower than previous level
                self.trailing_profit = computed_trailing

        return self.trailing_profit

    def reset_price_levels(self) -> None:
        """Set 'self.trailing_profit', 'self.ref_price', 'self.trigger_trail_level'
        and 'self.step_level' to None"""

        self.trailing_profit = None
        self.ref_price = None
        self.trigger_trail_level = None
        self.step_level = None
