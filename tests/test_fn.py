import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from strat_backtest.utils.dataframe_utils import display_dtypes, set_decimal_type
from strat_backtest.utils.file_utils import load_parquet
from strat_backtest.utils.time_utils import convert_tz, list_valid_tz


def test_fn():
    # df = pd.DataFrame(
    #     {
    #         "date": [
    #             pd.Timestamp(2025, 1, 1),
    #             pd.Timestamp(2025, 1, 2),
    #             pd.Timestamp(2025, 1, 3),
    #         ],
    #         "a x": [1.01, 1.02, 1.03],
    #         "b": [2.115, 2.251, 2.531],
    #         "c": [3.3311, 3.4422, 3.5533],
    #     }
    # )

    df = load_parquet("./data/AAPL.parquet")
    df_tz_aware = load_parquet("./data/AAPL.parquet", tz="Asia/Singapore")

    print(f"\n\ndf : \n\n{df}\n")
    print(f"df_tz_aware : \n\n{df_tz_aware}\n")

    print(f"{type(df.at[0, "Date"])=}")
    print(f"{type(df_tz_aware.at[0, "Date"])=}\n")

    print(f"{df.at[0, "Date"]=}")
    print(f"{df_tz_aware.at[0, "Date"]=}\n")
