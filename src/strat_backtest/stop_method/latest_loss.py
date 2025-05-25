"""Implementation of LatestLoss class

- Concrete implementation of 'StopLoss' abstract class
- Set stop price based on stop loss for the latest open position.
"""

from decimal import Decimal

from strat_backtest.base import StopLoss
from strat_backtest.utils.constants import OpenTrades
from strat_backtest.utils.pos_utils import get_std_field


class LatestLoss(StopLoss):
    """Compute stop price based on the percentage stop loss set
    for latest open trade. For example:

    - Long 50 (5 lots), 60 (3 lots), 70 (2 lots)
    - latest trade = 70 (2 lots)
    - If percentage loss is 20%, then stop price = 0.8 * 70 = 56
    """

    def cal_exit_price(self, open_trades: OpenTrades) -> Decimal:
        """Calculate stop price based on latest open position.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade containing open trades info.

        Returns:
            (Decimal): Exit price for all multiple open positions.
        """

        if len(open_trades) == 0:
            raise ValueError("'open_trades' cannot be empty.")

        # Get entry action and latest entry price
        entry_action = get_std_field(open_trades, "entry_action")
        latest_price = open_trades[-1].entry_price

        # Compute stop price to meet stipulated percent loss
        stop_price = (
            latest_price * (1 - self.percent_loss)
            if entry_action == "buy"
            else latest_price * (1 + self.percent_loss)
        )

        return Decimal(round(stop_price, 2))
