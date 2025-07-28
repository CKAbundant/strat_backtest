"""Helper function to run testing for 'FixedExit' class."""

import numpy as np
import pandas as pd

from tests.test_utils import convert_to_decimal


def gen_test_df(data: pd.DataFrame, stop_level: float) -> pd.DataFrame:
    """Append 'entry_date', 'entry_price' and 'stop' column to OHLCV DataFrame.

    Args:
        data (pd.DataFrame): DataFrame containing OHLCV data.
        stop_level (float): Amount of allowable loss per stock.

    Returns:
        df (pd.DataFrame): DataFrame with appended 'stop' column.
    """

    df = data.copy()

    # Raise error if both 'buy' and 'sell' are found in 'entry_signal' column
    entry_action = get_std_entry_action(df)

    # Append "entry_date" and "entry_price" column i.e. datetime and opening price for next
    # trading day
    last_date = df.iloc[-1]["date"]
    last_close = df.iloc[-1]["close"]
    df["entry_date"] = df["date"].shift(periods=-1, fill_value=last_date)
    df["entry_price"] = df["open"].shift(periods=-1, fill_value=last_close)

    # Append 'stop' column; and shift 1 row down i.e. stop level is meant for next trading day
    df["stop"] = (
        df["low"] - stop_level if entry_action == "buy" else df["high"] + stop_level
    )

    first_stop = df.at[0, "stop"]
    df["stop"] = df["stop"].shift(periods=1, fill_value=first_stop)

    # Convert numeric values into Decimal
    for col in df.columns:
        df[col] = df[col].map(convert_to_decimal)

    return df


def get_std_entry_action(df: pd.DataFrame) -> pd.DataFrame:
    """Raise error if both 'buy' and 'sell' are found in 'entry_signal' column."""

    ent_sig_set = set(df["entry_signal"].to_list())

    # Get standard entry signal (ignore 'wait')
    result_set = ent_sig_set - {"wait"}
    if len(result_set) > 1:
        raise ValueError("More than 1 expected signals present!")

    if (entry_action := next(iter(result_set))) not in {"buy", "sell"}:
        raise ValueError("Standard entry signal is neither 'buy' nor 'sell'.")

    return entry_action
