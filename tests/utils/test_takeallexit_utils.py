"""Utility function to test 'TakeAllExit' class."""

import random
from collections import deque
from datetime import timedelta
from decimal import Decimal

from strat_backtest.utils.constants import OpenTrades
from tests.utils.test_utils import update_open_pos


def update_open_trades(
    open_trades: OpenTrades,
    exit_lots_list: list[float],
) -> OpenTrades:
    """Update open trades based on 'is_partial' flag and 'entry_lots_list.

    Args:
        open_trades (OpenTrades):
            Deque list of StockTrade objects.
        exit_lots_list (list[float]):
            List of updated exit lots for OpenTrades.

    Returns:
        open_trades (OpenTrades): Updated open trades.
    """

    percent_change = Decimal(str(random.uniform(-0.02, 0.02)))
    updated_trades = deque()

    # Update exit lots based on 'exit_lots_list'
    for trade, exit_lots in zip(open_trades, exit_lots_list):
        next_day = trade.entry_datetime + timedelta(days=1)
        exit_price = round(trade.entry_price * (1 + percent_change), 2)

        # Update 'trade'
        updated_trades.append(update_open_pos(trade, next_day, exit_price, exit_lots))

    return updated_trades
