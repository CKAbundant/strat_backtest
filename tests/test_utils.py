"""Utility functions used in test scripts."""

from datetime import datetime
from decimal import Decimal

from strat_backtest.utils.constants import CompletedTrades, OpenTrades


def gen_takeallexit_completed_list(
    open_trades: OpenTrades, exit_dt: datetime, exit_price: float
) -> CompletedTrades:
    """Generated expected completed list for 'open_trades' based on
    'TakeAllExit' method.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'exit_all' method
    with the given parameters. Used for assertion comparisons in pytest.

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


def gen_exit_all_end_completed_list(
    open_trades: OpenTrades,
    completed_list: CompletedTrades,
    record: dict[str, Decimal | datetime],
) -> CompletedTrades:
    """Generate expected 'completed_list' via 'exit_all_end" method
    at end of trading period.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'exit_all_end' method
    with the given parameters. Used for assertion comparisons in pytests.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        completed_list (CompletedTrades):
            Initial list of dictionaries containing completed trades info just
            before end of trading period.
        record (dict[str, Decimal | datetime]):
            OHLCV info at end of trading period.

    Returns:
        expected_list (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
    """

    return completed_list.extend(
        gen_takeallexit_completed_list(record["date"], record["close"])
    )
