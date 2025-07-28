"""Generate test for concrete implementation of 'ExitStruct'."""

from datetime import datetime
from decimal import Decimal
from pprint import pformat

import pandas as pd
import pytest

from strat_backtest.exit_method import FixedExit
from tests.test_fixedexit_utils import gen_test_df


def test_update_exit_levels(sample_gen_trades):
    """Test if 'update_exit_levels' correctly updates 'exit_levels' attribute."""

    stop_level = 5

    # Generate test DataFrame
    df = sample_gen_trades.copy()
    df = gen_test_df(df, stop_level)
    print(f"\n\n{df}\n")

    # Intialize instance of FixedExit
    fixed_exit = FixedExit()

    for row in df.itertuples(index=False, name=None):
        info = {col: var for col, var in zip(df.columns, row)}

        if info["entry_signal"] == "buy":
            fixed_exit.update_exit_levels(
                info["entry_date"], info["entry_price"], info["stop"]
            )

    print(
        f"fixed_exit.exit_levels : \n\n{pformat(fixed_exit.exit_levels, sort_dicts=False)}\n"
    )

    assert fixed_exit.exit_levels == {
        datetime(2025, 4, 8, 0, 0): (Decimal("190.83"), Decimal("182.09")),
        datetime(2025, 4, 9, 0, 0): (Decimal("174.05"), Decimal("169.39")),
        datetime(2025, 4, 14, 0, 0): (Decimal("244.56"), Decimal("177.76")),
        datetime(2025, 4, 17, 0, 0): (Decimal("206.32"), Decimal("187.12")),
    }
