"""Abstract class to compute stop price for multiple open positions."""

from abc import ABC, abstractmethod
from decimal import Decimal

from strat_backtest.utils.constants import OpenTrades


class StopMethod(ABC):
    """Abstract class to generate exit price (i.e. either profit or stop loss)
    for multiple open positions based on price movement.

    Args:
        percent_loss (float):
            Percentage loss allowed for investment (Default: 0.2).

    Attributes:
        percent_loss (Decimal):
            Percentage loss allowed for investment (Default: 0.2).
    """

    def __init__(self, percent_loss: float = 0.2) -> None:
        self.percent_loss = Decimal(str(percent_loss))  # Convert to Decimal

    @abstractmethod
    def cal_exit_price(self, open_trades: OpenTrades) -> Decimal:
        """Calculate a single exit price for multiple open positions.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade containing open trades info.

        Returns:
            (Decimal): Exit price for all multiple open positions.
        """

        ...
