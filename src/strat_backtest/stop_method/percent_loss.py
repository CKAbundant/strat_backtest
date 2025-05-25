"""Implementation of PercentLoss class

- Concrete implementation of 'StopMethod' abstract class
- Compute stop price for all open position such that will result in losses
equal to pre-defined stop loss.
"""

from decimal import Decimal

from strat_backtest.base import StopMethod
from strat_backtest.utils.constants import OpenTrades
from strat_backtest.utils.pos_utils import get_net_pos, get_std_field


class PercentLoss(StopMethod):
    """Compute stop price such that total loss for all open positions
    is within the accepted percent loss. For example:

    - Long 50 (5 lots), 60 (3 lots), 70 (2 lots).
    - If percentage loss is 20%, then stop price = 57
    - 57 * 8 (total lots) = 352 = 80% of total investment of 570
    """

    def cal_exit_price(self, open_trades: OpenTrades) -> Decimal:
        """Calculate stop price to meet percent loss for total investment.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade containing open trades info.

        Returns:
            (Decimal): Exit price for all multiple open positions.
        """

        entry_action = get_std_field(open_trades, "entry_action")

        # Current investment = investment value of current open positions
        cur_invest = sum(
            trade.entry_price * (trade.entry_lots - trade.exit_lots)
            for trade in open_trades
        )

        # Total number of open position
        total_open = get_net_pos(open_trades)

        # Compute stop price to meet stipulated percent loss
        stop_price = (
            cur_invest * (1 - self.percent_loss) / total_open
            if entry_action == "buy"
            else cur_invest * (1 + self.percent_loss) / total_open
        )

        return round(stop_price, 2)
