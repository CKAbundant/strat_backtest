"""Helper functions to load and save files in required format."""

from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd


def create_folder(data_dir: str | Path) -> None:
    """Create folder if not exist."""

    data_dir = Path(data_dir)

    if not data_dir.is_dir():
        data_dir.mkdir(parents=True, exist_ok=True)


def save_csv(df: pd.DataFrame, file_path: str, save_index: bool = False) -> None:
    """Convert numeric columns to Decimal type before saving DataFrame
    as csv file."""

    # Get numeric columns
    num_cols = df.select_dtypes(include=np.number).columns.to_list()

    # Convert numbers to Decimal type
    for col in num_cols:
        df[col] = df[col].map(lambda num: Decimal(str(num)))

    # Save DataFrame as 'trade_results.csv'
    df.to_csv(file_path, index=save_index)


def load_csv(
    file_path: str,
    header: list[int] | None = "infer",
    index_col: list[int] | None = None,
    tz: str | None = None,
) -> pd.DataFrame:
    """Load DataFrame and convert numeric columns to Decimal type.

    Args:
        file_path (str):
            Relative patht to csv file.
        header (list[int] | str):
            If provided, list of row numbers containing column labels
            (Default: "infer").
        index_col (list[int] | None):
            If provided, list of columns to use as row labels.
        tz (str | None):
            If provided, timezone for datetime object e.g. "America/New_York".

    Returns:
        df (pd.DataFrame): Loaded DataFrame (including multi-level).
    """

    # Load DataFrame from 'trade_results.csv'
    df = pd.read_csv(file_path, header=header, index_col=index_col)

    # Ensure all numbers are set to Decimal type and all dates are set
    # to datetime.date type
    df = set_decimal_type(df)
    df = set_date_type(df, tz)

    if isinstance(header, list):
        # Remove 'Unnamed' from multi-level columns
        return remove_unnamed_cols(df)

    return df


def set_decimal_type(data: pd.DataFrame, to_round: bool = False) -> pd.DataFrame:
    """Ensure all numeric types in DataFrame are Decimal type.

    Args:
        DataFrame (pd.DataFrame):
            Both normal and multi-level columns DataFrame.
        to_round (bool):
            Whether to round float to 6 decimal places before converting to
            Decimal (Default: False).

    Returns:
        df (pd.DataFrame): DataFrame containing numbers of Decimal type only.
    """

    df = data.copy()

    for col in df.columns:
        # Column is float type and does not contain any missing values
        if df[col].dtypes == float and not df[col].isna().any():
            df[col] = df[col].map(
                lambda num: (
                    Decimal(str(round(num, 6))) if to_round else Decimal(str(num))
                )
            )

        # Column is float type and contain missing values
        elif df[col].dtypes == float and df[col].isna().any():
            df[col] = [Decimal(str(num)) if np.isnan(num) else num for num in df[col]]

    return df


def set_date_type(data: pd.DataFrame, tz: str | None = None) -> pd.DataFrame:
    """Ensure all datetime objects in DataFrame are set to datetime.date type.

    Args:
        data (pd.DataFrame): DataFrame containing date related columns.
        tz (str | None): If provided, timezone for datetime e.g. "America/New_York".

    Returns:
        (pd.DataFrame): DataFrame with date related columns set to datetime type.
    """

    df = data.copy()

    # Check if 'date' is found in column for nomral and multi-level DataFrame
    date_cols = [
        col
        for col in df.columns
        if (isinstance(col, str) and "date" in col.lower())
        or (isinstance(col, tuple) and "date" in col[0].lower())
    ]

    # Convert date to datetime type
    for col in date_cols:
        if tz:
            df[col] = pd.to_datetime(df[col], utc=True)
            df[col] = df[col].dt.tz_convert(tz)
        else:
            df[col] = pd.to_datetime(df[col])

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


# Public Interface
__all__ = [
    "create_folder",
    "load_csv",
    "save_csv",
    "set_decimal_type",
]
