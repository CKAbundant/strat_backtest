"""Generic helper functions. For example:

- Manipulate DataFrame
- Format display via print
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from strat_backtest.utils.constants import OpenTrades, PriceAction, Record


def display_open_trades(open_trades: OpenTrades, var_name: str | None = None) -> None:
    """Omit 'days_held', 'profit_loss', 'percent_ret', 'daily_ret'
    and 'win' fields in StockTrade."""

    # Set name of variable as 'open_trades' if not provided
    var_name = var_name or "open_trades"

    if len(open_trades) == 0:
        print(f"{var_name} : []\n")
        return None

    msg_list = []
    for trade in open_trades:
        entry_date = trade.entry_datetime.strftime("%Y-%m-%d")
        exit_date = (
            f"\"{trade.exit_datetime.strftime('%Y-%m-%d')}\""
            if trade.exit_datetime
            else "None"
        )
        exit_action = f"'{trade.exit_action}'" if trade.exit_action else "None"

        trade_str = (
            "   {\n"
            f"      ticker: '{trade.ticker}', "
            f"ent_dt: '{entry_date}', "
            f"ent_act: '{trade.entry_action}', "
            f"ent_lots: {trade.entry_lots}, "
            f"ent_price: {trade.entry_price}, "
            f"ex_dt: {exit_date}, "
            f"ex_act: {exit_action}, "
            f"ex_lots: {trade.exit_lots}, "
            f"ex_price: {trade.exit_price}"
            "\n   },"
        )
        msg_list.append(trade_str)

    msg = "\n".join(msg_list)

    print(f"{var_name} : \n[\n{msg}\n]\n")

    return None


def convert_to_decimal(var: Any | None) -> Decimal | None:
    """Convert 'var' to Decimal type if numeric type."""

    if var is None:
        return None

    if not isinstance(var, (int, float, Decimal)):
        return var

    return Decimal(str(var))


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


# Public Interface
__all__ = [
    "display_open_trades",
    "convert_to_decimal",
    "gen_cond_list",
]
