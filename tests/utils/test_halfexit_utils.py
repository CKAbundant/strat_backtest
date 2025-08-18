"""Helper function to run testing for 'HalfFIFOExit' and 'HalfLIFOExit' class."""

from collections import deque
from datetime import datetime
from decimal import Decimal

from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.utils.constants import ClosedPositionResult, OpenTrades
from tests.utils.test_utils import update_open_pos


def gen_half_fifoexit_closedpositionresult(
    open_trades: OpenTrades, dt: datetime, op: Decimal
) -> ClosedPositionResult:
    """Generate the expected open trades and completed trade list for 'HalfFIFOExit'."""

    expected_list = []
    expected_trades = deque()

    for trade in open_trades.copy():
        open_lots = trade.entry_lots - trade.exit_lots

        if half_completed <= 0:
            # Existing position is reduced by half hence append remaining trades
            # as open positions
            expected_trades.append(trade)
            continue

        if open_lots <= half_completed:
            # Number of lots is less than required half position hence
            # close off current trade
            completed_trade = update_open_pos(trade.model_copy(), dt, op)
            expected_list.append(completed_trade.model_dump())

            # Reduce required lots by open lots in current trade
            half_completed -= open_lots

        else:
            # Close open position by 'half_position' as number of open lots
            # more than required half position. Ensure entry lots equal exit lots.
            completed_trade = update_open_pos(
                trade.model_copy(),
                dt,
                op,
                exit_lots=half_completed,
            )
            completed_trade.entry_lots = completed_trade.exit_lots

            # Update trade to reflect partal close
            open_trade = update_open_pos(
                trade.model_copy(),
                dt,
                op,
                exit_lots=trade.exit_lots + half_completed,
            )

            expected_list.append(completed_trade.model_dump())
            expected_trades.append(open_trade)
            half_completed = 0
