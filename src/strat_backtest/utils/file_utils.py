"""Helper functions to load and save files in required format."""

from pathlib import Path

import pandas as pd

from strat_backtest.utils.dataframe_utils import (convert_tz_aware,
                                                  remove_unnamed_cols,
                                                  set_decimal_type,
                                                  set_naive_tz)


def create_folder(data_dir: str | Path) -> None:
    """Create folder if not exist."""

    data_dir = Path(data_dir)

    if not data_dir.is_dir():
        data_dir.mkdir(parents=True, exist_ok=True)


def save_csv(
    df: pd.DataFrame, file_path: str | Path, save_index: bool = False, dec_pl: int = 6
) -> None:
    """Convert numeric columns to Decimal type before saving DataFrame
    as csv file."""

    # Convert numbers to Decimal type
    df = set_decimal_type(df, dec_pl)

    # Save DataFrame as 'trade_results.csv'
    df.to_csv(file_path, index=save_index)


def load_csv(
    file_path: str | Path,
    header: list[int] | None = "infer",
    index_col: list[int] | None = None,
    tz: str | None = None,
) -> pd.DataFrame:
    """Load DataFrame from csv file and convert numeric columns to Decimal type.

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

    # Ensure all numbers are set to Decimal type
    df = set_decimal_type(df)

    if tz:
        # Set timezone aware
        df = convert_tz_aware(df, tz)
    else:
        # Set timezone naive
        df = set_naive_tz(df)

    if isinstance(header, list):
        # Remove 'Unnamed' from multi-level columns
        return remove_unnamed_cols(df)

    return df


def load_parquet(file_path: str | Path, tz: str | None = None) -> pd.DataFrame:
    """Load DataFrame from parquet file and convert numeric columns to Decimal type."""

    # Load DataFrame from 'trade_results.csv'
    df = pd.read_parquet(file_path)

    # Reset index if index name is not None
    if df.index.name is not None:
        df = df.reset_index()

    # Ensure all numbers are set to Decimal type
    df = set_decimal_type(df)

    if tz:
        # Set timezone aware
        df = convert_tz_aware(df, tz)
    else:
        # Set timezone naive
        df = set_naive_tz(df)

    return df


# Public Interface
__all__ = [
    "create_folder",
    "load_csv",
    "save_csv",
    "load_parquet",
]
