"""Generic utility functions used in test scripts."""

from collections import deque
from datetime import datetime
from decimal import Decimal

import pandas as pd

from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.utils.constants import CompletedTrades, OpenTrades, Record
from strat_backtest.utils.utils import convert_to_decimal, correct_datatype


def get_latest_record(df_sample: pd.DataFrame) -> Record:
    """Generate dictionary from last record in sample DataFrame."""

    record = df_sample.iloc[-1, :].to_dict()

    return correct_datatype(record)


def get_date_record(df_sample: pd.DataFrame, dt: str | datetime) -> Record:
    """Generate dictionary for record with required datetime."""

    df = df_sample.copy()

    if isinstance(dt, str):
        # Convert to datetime type
        dt = datetime.strptime(dt, "%Y-%m-%d")

    if dt not in df_sample["date"].to_list():
        raise ValueError(f"'{dt}' is an invalid date!")

    record = df.loc[df["date"] == dt, :].to_dict(orient="records")[0]

    return correct_datatype(record)


def gen_record(df_sample: pd.DataFrame, **kwargs) -> Record:
    """Generate dictionary with desired key-value pair to intialize 'Record'
    (if provided).

    Args:
        df_sample (pd.DataFrame):
            Sample of signals DataFrame, which contains 'exit_signal' column.
        **kwargs (Any):
            Columns in 'df_sample' and its corresponding value.

    Returns:
        (dict[str, str | Decimal]):
            Selected single record in 'df_sample' converted to dictionary.
    """

    # Get latest record from sample DataFrame
    record = get_latest_record(df_sample)

    for col, value in kwargs.items():
        record[col] = value

    return correct_datatype(record)


def update_open_pos(
    trade: StockTrade,
    exit_dt: datetime | pd.Timestamp,
    exit_price: float,
    exit_lots: float | None = None,
) -> StockTrade:
    """Update open position with exit datetime and price."""

    entry_lots = trade.entry_lots
    exit_lots = exit_lots or entry_lots

    # Get 'exit_action' based on 'entry_action'
    exit_action = "sell" if trade.entry_action == "buy" else "buy"

    # Ensure 'exit_dt' is datetime type
    if isinstance(exit_dt, pd.Timestamp):
        exit_dt = exit_dt.to_pydatetime()

    updated_trade = trade.model_copy()

    updated_trade.exit_datetime = exit_dt
    updated_trade.exit_action = exit_action
    updated_trade.exit_lots = exit_lots
    updated_trade.exit_price = convert_to_decimal(exit_price)

    return updated_trade


def create_new_pos(
    record: Record,
    num_lots: int,
    open_trades: OpenTrades = deque(),
) -> OpenTrades:
    """Update 'open_trades' with trade info from 'record'."""

    dt = (
        record["date"]
        if isinstance(record["date"], datetime)
        else record["date"].to_pydatetime()
    )
    entry_signal = record["entry_signal"]
    entry_price = record["open"]  # Assume create new position at open price

    new_pos = StockTrade(
        ticker="AAPL",
        entry_datetime=dt,
        entry_action=entry_signal,
        entry_lots=convert_to_decimal(num_lots),
        entry_price=convert_to_decimal(entry_price),
    )

    open_trades.append(new_pos)

    return open_trades


def get_open_lots(open_trades: OpenTrades) -> Decimal:
    """Count number of open lots in 'open_trades'."""

    return sum(trade.entry_lots - trade.exit_lots for trade in open_trades)


def get_completed_lots(completed_list: CompletedTrades) -> Decimal:
    """Count number of completed lots in 'completed_list'"""

    # Check if entry lots == exit lots for each StockTrade item in 'completed_list'
    if any(trade["entry_lots"] != trade["exit_lots"] for trade in completed_list):
        raise ValueError("Number of entry lots not equal to exit lots")

    return sum(trade["exit_lots"] for trade in completed_list)
