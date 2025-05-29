"""Implementation of NearestLoss class

- Concrete implementation of 'StopLoss' abstract class
- Set stop price based on the stop loss for the open position that is closest
to current trading price.
"""

from decimal import Decimal

from strat_backtest.base import StopLoss
from strat_backtest.utils.constants import OpenTrades
from strat_backtest.utils.pos_utils import get_std_field


class NearestLoss(StopLoss):
    """Use stop price (based on the percentage loss) that is nearest to
    current monitor price. For example:

    - Long 50 (5 lots),  70 (2 lots), 60 (3 lots)
    - Closest stop price for each position = [40, 56, 48]
    - Nearest stop price to current close = 56
    """

    def cal_exit_price(self, open_trades: OpenTrades) -> Decimal:
        """Use highest stop price for long position and lowest stop price
        for short position.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade containing open trades info.

        Returns:
            (Decimal): Exit price for all multiple open positions.
        """

        if len(open_trades) == 0:
            raise ValueError("'open_trades' cannot be empty.")

        # Get entry action
        entry_action = get_std_field(open_trades, "entry_action")

        # Generate list of stop price for each open position
        stop_list = [
            (
                trade.entry_price * (1 - self.percent_loss)
                if entry_action == "buy"
                else trade.entry_price * (1 + self.percent_loss)
            )
            for trade in open_trades
        ]

        # Use highest stop price for long position and lowest stop price
        # for short position
        stop_price = max(stop_list) if entry_action == "buy" else min(stop_list)

        return round(stop_price, 2)
