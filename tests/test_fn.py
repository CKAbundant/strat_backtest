from decimal import Decimal

import pandas as pd

from strat_backtest.utils import convert_to_datetime
from strat_backtest.utils.time_utils import validate_dayfirst


def test_fn():
    # data = pd.DataFrame(
    #     {"A": ["2025-08-01", "2025-08-02"], "B": ["2024-01-01", "invalid"]}
    # )
    # print(f"\n\n{data}\n")

    user_dayfirst = True
    print(f"\n\n{user_dayfirst=}\n")

    var_list = [
        "10/30/2025",
        "10/1/2025",
        "10 Sep 2025",
        "95-01-01",
        "95-1-1",
        "195-1-1",
        "15-15-1",
        "1-15-15",
        "15-1-15",
        1234567890,
        12345678.2222,
        Decimal("111"),
    ]

    for var in var_list:
        dt_var = convert_to_datetime(var, user_dayfirst)

        print(f"{dt_var=}")
