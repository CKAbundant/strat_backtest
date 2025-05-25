"""Implementation of FirstTrail class

- Concrete implementation of 'TrailProfit' abstract class
- Set trigger trail level based on first open position.
"""

from datetime import datetime
from decimal import Decimal

from strat_backtest.base import TrailProfit
from strat_backtest.utils.constants import OpenTrades
from strat_backtest.utils.pos_utils import get_std_field


class FirstTrail(TrailProfit):
    """Compute trailing profit price by setting trigger trail level
    based on first open position.

    - Long 50 (5 lots), 60 (3 lots), 70 (2 lots)
    - trigger_trail_level = 50 (first open position) * (1 + trigger_trail)
    """

    def cal_trail_price(
        self, open_trades: OpenTrades, record: dict[str, Decimal | datetime]
    ) -> Decimal:
        """Calculate trail price based on first open position.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade containing open trades info.
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.

        Returns:
            (Decimal): Trailing profit price for all multiple open positions.
        """

        if len(open_trades) == 0:
            raise ValueError("'open_trades' cannot be empty.")

        # Use entry price for first open position as reference price
        first_price = open_trades[0].entry_price

        # Get standard 'entry_action' from 'self.open_trades'
        entry_action = get_std_field(open_trades, "entry_action")

        # Re-compute 'self.trigger_trail_level' and 'self.step_level' if reference price
        # changes
        if self.ref_price != first_price:
            # Ensure price levels e.g. 'trailing_profit' are set to None
            self.reset_price_levels()

            # Update 'ref_price' with current 'first_price'
            self.ref_price = first_price

            # Compute trigger trail price level based on updated reference price
            self.trigger_trail_level = self._cal_trigger_trail_level(entry_action)

            # Compute price increment level to shift trailing profit
            self.step_level = (
                self.ref_price * self.step if self.step is not None else None
            )

        # Compute trailing profit
        return self._cal_trailing_profit(record, entry_action)
