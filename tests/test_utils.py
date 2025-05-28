"""Utility functions used in test scripts."""

from datetime import datetime

from strat_backtest.utils.constants import CompletedTrades, OpenTrades


def gen_takeall_completed_list(
    open_trades: OpenTrades, exit_dt: datetime, exit_price: float
) -> CompletedTrades:
    """Generated expected completed list for 'open_trades' based on
    'TakeAllExit' method.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        exit_dt (datetime):
            Datetime object when open position is closed.

    Returns:
        expected_list (CompletedTrades):
            List of dictionaries containing completed trades info.
    """

    expected_list = []

    for open_pos in open_trades:
        # Create shallow copy of open position
        pos = open_pos.model_copy()

        # Update 'completed_pos' with exit info, ensuring positions
        # are properly closed
        pos.exit_datetime = exit_dt
        pos.exit_action = "sell" if pos.entry_action == "buy" else "buy"
        pos.exit_lots = pos.entry_lots
        pos.exit_price = exit_price

        expected_list.append(pos.model_dump())

    return expected_list
