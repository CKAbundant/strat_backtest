"""Helper functions used directly in position management."""

import importlib
from collections import Counter, deque
from datetime import datetime
from decimal import Decimal
from typing import Any, Type, TypeVar

import pandas as pd

from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.utils.constants import (
    CompletedTrades,
    OpenTrades,
    PriceAction,
    Record,
)
from strat_backtest.utils.utils import convert_to_decimal

# Create generic type variable 'T'
T = TypeVar("T")


def get_class_instance(
    class_name: str, module_path: str, **params: dict[str, Any]
) -> T:
    """Return instance of a class that is initialized with 'params'.

    Args:
        class_name (str):
            Name of class to create an instance.
        module_path (str):
            Module path relative from main package e.g.
            strat_backtest.base.entry_struct.
        **params (dict[str, Any]):
            Arbitrary Keyword input arguments to initialize class instance.

    Returns:
        (T): Initialized instance of class.
    """

    try:
        # Import python script at class path as python module
        module = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(f"Invalid module path : '{module_path}'") from e

    try:
        # Get class from module
        req_class: Type[T] = getattr(module, class_name)
    except AttributeError as e:
        raise AttributeError(f"'{class_name}' class is not found in module") from e

    # Intialize instance of class
    return req_class(**params)


def get_net_pos(open_trades: tuple[StockTrade] | OpenTrades) -> int:
    """Get net positions from 'self.open_trades'."""

    return sum(
        (
            trade.entry_lots - trade.exit_lots
            if trade.entry_action == "buy"
            else -(trade.entry_lots - trade.exit_lots)
        )
        for trade in open_trades
    )


def get_std_field(open_trades: OpenTrades, std_field: str) -> Any:
    """Get standard field (i.e. 'ticker' or 'entry_action') from 'open_trades'."""

    counter = Counter([getattr(trade, std_field) for trade in open_trades])

    if len(counter) > 1:
        raise ValueError(f"'{std_field}' field is not consistent.")

    return list(counter.keys())[0] if len(open_trades) > 0 else None


def gen_completed_trade(trade: StockTrade, lots_to_exit: Decimal) -> CompletedTrades:
    """Generate StockTrade object with completed trade from 'StockTrade'
    and convert to dictionary."""

    # Create a shallow copy of the updated trade
    completed_trade = trade.model_copy()

    # Update the 'entry_lots' and 'exit_lots' to be same as 'lots_to_exit'
    completed_trade.entry_lots = lots_to_exit
    completed_trade.exit_lots = lots_to_exit

    if not validate_completed_trades(completed_trade):
        raise ValueError("Completed trades not properly closed.")

    return completed_trade.model_dump()


def validate_completed_trades(stock_trade: StockTrade) -> bool:
    """Validate whether StockTrade object is properly updated with no null
    values."""

    # Check for null fields
    is_no_null_field = all(
        field is not None for field in stock_trade.model_dump().values()
    )

    # Check if number of entry lots must equal number of exit lots
    is_lots_matched = stock_trade.entry_lots == stock_trade.exit_lots

    return is_no_null_field and is_lots_matched


def gen_cond_list(
    record: Record,
    entry_action: PriceAction,
    trigger_price: Decimal,
    monitor_close: bool,
) -> tuple[bool, list[bool]]:
    """Generate 2 list of conditions to trigger action upon market opening;
    and after market opening.

    Args:
        record (Record):
            Dictionary containing OHLC info and entry/exit signal.
        entry_action (PriceAction):
            Standard entry action for existing open positions.
        trigger_price (Decimal):
            Price level to trigger action.
        monitor_close (bool):
            Whether to monitor close price ("close") or both high and low price.

    Returns:
        open_cond (list[bool]):
            Conditions to trigger upon market opening.
        trigger_cond_list (list[bool]):
            List of conditions to trigger after market opening.
    """

    op = record.get("open")
    high = record.get("high")
    low = record.get("low")
    close = record.get("close")

    # Check if stop loss triggered upon market opening
    open_cond = (
        entry_action == "buy"
        and op <= trigger_price
        or entry_action == "sell"
        and op >= trigger_price
    )

    # List of stop loss conditions
    trigger_cond_list = [
        monitor_close and entry_action == "buy" and close <= trigger_price,
        monitor_close and entry_action == "sell" and close >= trigger_price,
        not monitor_close and entry_action == "buy" and low <= trigger_price,
        not monitor_close and entry_action == "sell" and high >= trigger_price,
    ]

    return open_cond, trigger_cond_list


def correct_datatype(record: Record) -> dict[str, datetime | str | Decimal]:
    """Ensure OHLCV are decimal type and date is datetime object."""

    return {
        k: v.to_pydatetime() if isinstance(v, pd.Timestamp) else convert_to_decimal(v)
        for k, v in record.items()
    }


def reverse_deque_list(deque_list: deque[list[Any]]) -> deque[list[Any]]:
    """Reverse sequence in deque list."""

    reverse_list = list(deque_list)[::-1]

    return deque(reverse_list)


# Public Interface
__all__ = [
    "get_class_instance",
    "get_net_pos",
    "get_std_field",
    "gen_completed_trade",
    "validate_completed_trades",
]
