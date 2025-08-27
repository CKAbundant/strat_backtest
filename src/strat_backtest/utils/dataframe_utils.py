"""Utility functions to handle all DataFrame related operations."""

from datetime import datetime

import pandas as pd

from strat_backtest.utils.time_utils import convert_to_datetime, convert_tz
from strat_backtest.utils.utils import convert_to_decimal


def get_date_cols(df: pd.DataFrame) -> list[str]:
    """Get list of columns that are of date type i.e.
    datetime object or Pandas timestamp object."""

    # Reset index if index name is not None
    if df.index.name is not None:
        df = df.reset_index()

    date_cols = []

    for col in df.columns:
        # Get list of unique data types for each column
        datatype_set = {type(rec) for rec in df[col]}

        # Check if record in columns are either datetime or pd.Timestamp object
        if datatype_set & {pd.Timestamp, datetime}:
            date_cols.append(col)

    return date_cols


def set_datetime(data: pd.DataFrame) -> pd.DataFrame:
    """Ensure date-related columns including properly formatted date strings
    are converted to datetime objects"""

    df = data.copy()

    for col in df.columns:
        df[col] = df[col].map(convert_to_datetime)

    return df


def set_decimal_type(data: pd.DataFrame, dec_pl: int = 6) -> pd.DataFrame:
    """Ensure all numeric types in DataFrame are Decimal type.

    Args:
        DataFrame (pd.DataFrame):
            Both normal and multi-level columns DataFrame.
        dec_pl (int | None):
            Number of decimal places to round numeric variable (Default: 6).

    Returns:
        df (pd.DataFrame): DataFrame containing numbers of Decimal type only.
    """

    df = data.copy()

    for col in df.columns:
        df[col] = df[col].map(lambda record: convert_to_decimal(record, dec_pl))

    return df


def set_naive_tz(data: pd.DataFrame, reset_time: bool = False) -> pd.DataFrame:
    """Set all date-related columns to be time zone naive."""

    df = data.copy()

    # Ensure date-related columns are converted to datetime objects
    df = set_datetime(df)

    # Check for columns contain date type records
    date_cols = get_date_cols(df)

    if not date_cols:
        raise ValueError("No columns contain date objects found.")

    # Set date type column to timezone naive
    for col in date_cols:
        df[col] = pd.to_datetime(df[col])

        if reset_time:
            df[col] = df[col].map(lambda dt: dt.replace(hour=0, minute=0, tzinfo=None))
        else:
            df[col] = df[col].map(lambda dt: dt.replace(tzinfo=None))

    return df


def convert_tz_aware(data: pd.DataFrame, tz: str) -> pd.DataFrame:
    """Convert date-related columns to be time zone aware."""

    df = data.copy()

    # Ensure date-related columns are converted to datetime objects
    df = set_datetime(df)

    # Check for columns contain date type records
    date_cols = get_date_cols(df)

    if not date_cols:
        raise ValueError("No columns contain date objects found.")

    for col in date_cols:
        df[col] = pd.to_datetime(df[col])
        df[col] = df[col].map(lambda dt: convert_tz(dt, tz))

    return df


def set_as_index(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Set 'col' column as index for DataFrame."""

    if col not in df.columns:
        raise ValueError(
            f"'{col}' column is not found. Hence it can't be set as index."
        )

    df = df.set_index(col)

    return df


def remove_unnamed_cols(data: pd.DataFrame) -> pd.DataFrame:
    """Set column label containing 'Unnamed:' to empty string for multi-level
    columns DataFrame."""

    df = data.copy()
    formatted_cols = []

    if any(isinstance(col, str) for col in df.columns):
        # No amendments made since columns are not multi-level
        return df

    for col_tuple in df.columns:
        col_levels = []
        for col in col_tuple:
            if "unnamed:" in col.lower():
                col_levels.append("")
            else:
                col_levels.append(col)
        formatted_cols.append(col_levels)

    df.columns = pd.MultiIndex.from_tuples(formatted_cols)

    return df


def display_dtypes(data: pd.DataFrame, name: str | None = None) -> pd.DataFrame:
    """Display the different data types present for each column in DataFrame."""

    msg = "" if name is None else f"'{name}' "

    print(f"\n\nList of datatypes for each column in {msg}DataFrame :\n")

    for col in data.columns:
        dtype_list = list({str(type(col)) for col in data[col]})
        dtype_msg = (", ").join(dtype_list)

        print(f"{col:<15} : {dtype_msg}")


__all__ = [
    "get_date_cols",
    "set_decimal_type",
    "set_naive_tz",
    "convert_tz_aware",
    "set_as_index",
    "display_dtypes",
    "set_datetime",
]
