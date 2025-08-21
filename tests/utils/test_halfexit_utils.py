"""Helper function to run testing for 'HalfFIFOExit' and 'HalfLIFOExit' class."""

import math
import random
from collections import deque
from datetime import datetime, timedelta
from decimal import Decimal
from pprint import pformat

import pandas as pd

from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.utils.constants import (
    ClosedPositionResult,
    CompletedTrades,
    OpenTrades,
    Record,
)
from tests.utils.test_utils import get_open_lots, update_open_pos


def gen_completed_trade(
    trade: StockTrade, record: Record, open_lots: Decimal, required_lots: Decimal
) -> dict[str, str | Decimal | datetime]:
    """Generate the completed trades by reducing existing positions by half.

    Args:
        trade (StockTrade):
            Pydantic object containing OHLC information.
        record (Record):
            Dictionary containing OHLC info.
        open_lots (Decimal):
            Number of lots open for existing StockTrade object.
        required_lots (Decimal):
            Required number of lots to close to achieve half position.

    Returns:
        completed_trade (CompletedTrades):
            Dictionary containing updated stock info after closing by half lots.
    """

    dt = record["date"]
    exit_price = record["open"]  # Exit at opening price

    if required_lots == 0:
        # No action take since have exited required lots
        return []

    if open_lots <= required_lots:
        # Closed fully since open lots less than required lots
        completed_trade = update_open_pos(trade, dt, exit_price, exit_lots=open_lots)

    elif open_lots > required_lots:
        # Partial close since open_lots more than required lots
        completed_trade = update_open_pos(
            trade, dt, exit_price, exit_lots=required_lots
        )

    # Ensure entry lots equal exit lots
    completed_trade.entry_lots = completed_trade.exit_lots

    # Convert completed_trade to dictionary
    completed_trade = [completed_trade.model_dump()]

    return completed_trade


def gen_open_trade(
    trade: StockTrade, record: Record, open_lots: Decimal, required_lots: Decimal
) -> StockTrade | None:
    """Generate open trades after reducing existing positions by half.

    Args:
        trade (StockTrade):
            Pydantic object containing OHLC information.
        record (Record):
            Dictionary containing OHLC info.
        open_lots (Decimal):
            Number of lots open for existing StockTrade object.
        required_lots (Decimal):
            Required number of lots to close to achieve half position.

    Returns:
        expected_trade (StockTrade | None):
            If provided, list containing updated StockTrade object.
    """

    dt = record["date"]
    exit_price = record["open"]  # Exit at opening price

    if required_lots == 0:
        # All required lots closed hence trade unchanged
        expected_trade = trade.model_copy()

    elif open_lots <= required_lots:
        # Update trade to close all open position
        expected_trade = None

    elif open_lots > required_lots:
        # Partial close trade by 'required_lots'
        expected_trade = update_open_pos(
            trade.model_copy(), dt, exit_price, exit_lots=required_lots
        )

    return expected_trade


def update_required_lots(open_lots: Decimal, required_lots: Decimal) -> Decimal:
    """Reduce 'required_lots' if number of open lots is less than or equal
    to 'required_lots' else set 'required_lots' to 0"""

    if open_lots <= required_lots:
        # Close all open trades in trade
        required_lots -= open_lots

    else:
        # All required lots closed since current trade has enough open positions
        required_lots = 0

    return required_lots


def gen_half_fifo_closedpositionresult(
    open_trades: OpenTrades, record: Record
) -> ClosedPositionResult:
    """Generate open trades and completed trades by reducing half lots via FIFO."""

    expected_list = []

    # Compute expected open trades by removing half of the earliest existing open position
    total_open = get_open_lots(open_trades)
    required_lots = math.ceil(total_open / 2)

    expected_list = []
    expected_trades = deque()

    for trade in open_trades.copy():
        open_lots = trade.entry_lots - trade.exit_lots

        if open_trade := gen_open_trade(
            trade.model_copy(), record, open_lots, required_lots
        ):
            # Update 'expected_trades' if not all lots closed for StockTrade object.
            expected_trades.append(open_trade)

        # Update 'expected_list' if all lots closed for StockTrade object
        expected_list.extend(
            gen_completed_trade(trade.model_copy(), record, open_lots, required_lots)
        )

        # Update 'required_lots' after closing any open position
        required_lots = update_required_lots(open_lots, required_lots)

    return expected_trades, expected_list


def gen_half_lifo_closedpositionresult(
    open_trades: OpenTrades, record: Record
) -> ClosedPositionResult:
    """Generate open trades and completed trades by reducing half lots via LIFO."""

    expected_list = []

    # Compute expected open trades by removing half of the earliest existing open position
    total_open = get_open_lots(open_trades)
    required_lots = math.ceil(total_open / 2)

    expected_list = []
    expected_trades = deque()

    # Reverse order for 'open_trades'
    reversed_trades = list(open_trades.copy())[::-1]

    for trade in reversed_trades:
        open_lots = trade.entry_lots - trade.exit_lots

        if open_trade := gen_open_trade(
            trade.model_copy(), record, open_lots, required_lots
        ):
            # Update 'expected_trades' if not all lots closed for StockTrade object.
            expected_trades.appendleft(open_trade)

        # Update 'expected_list' if all lots closed for StockTrade object
        expected_list.extend(
            gen_completed_trade(trade.model_copy(), record, open_lots, required_lots)
        )

        # Update 'required_lots' after closing any open position
        required_lots = update_required_lots(open_lots, required_lots)

    return expected_trades, expected_list


def update_open_trades(
    open_trades: OpenTrades,
    entry_lots_list: list[float],
    is_partial: bool,
    is_fifo: bool,
) -> OpenTrades:
    """Update open trades based on 'is_partial' flag and 'entry_lots_list.

    Args:
        open_trades (OpenTrades):
            Deque list of StockTrade objects.
        entry_lots_list (list[float]):
            List of updated entry lots for OpenTrades.
        is_partial (bool):
            Whether to update the opentrades with partial fill i.e.
            0 < exit_lots < entry_lots.
        is_fifo (bool):
            Whether FIFO or not.

    Returns:
        open_trades (OpenTrades): Updated open trades.
    """

    percent_change = 0.02

    # Get 1 day later from date of first record for FIFO or date of
    # last record for LIFO
    if is_fifo:
        next_day = open_trades[0].entry_datetime + timedelta(days=1)
        exit_price = round(
            open_trades[0].entry_price * Decimal(str(1 + percent_change)), 2
        )

    else:
        next_day = open_trades[-1].entry_datetime + timedelta(days=1)
        exit_price = round(
            open_trades[-1].entry_price * Decimal(str(1 + percent_change)), 2
        )

    # Update partial lots closed if 'is_partial' is True
    if is_partial:
        first_entry_lots = open_trades[0].entry_lots
        open_trades[0] = update_open_pos(
            open_trades[0],
            exit_dt=next_day,
            exit_price=exit_price,
            exit_lots=random.choice(list(range(1, entry_lots_list[0]))),
        )

    # Update entry lots based on 'entry_lots_list'
    for trade, entry_lots in zip(open_trades, entry_lots_list):
        trade.entry_lots = entry_lots

    return open_trades
