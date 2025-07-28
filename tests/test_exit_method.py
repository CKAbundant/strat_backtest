"""Generate test for concrete implementation of 'ExitStruct'."""

from collections import deque
from datetime import datetime
from decimal import Decimal
from pprint import pformat

import pandas as pd
import pytest

from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.exit_method import FixedExit
from strat_backtest.utils.utils import display_open_trades
from tests.test_fixedexit_utils import gen_test_df
from tests.test_utils import get_latest_record


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


@pytest.mark.parametrize("entry_dt", [datetime(2025, 4, 9), None])
def test_close_pos_invalid_dates(sample_gen_trades, open_trades, entry_dt):
    """Test if 'close_pos' raise KeyError for invalid entry dates."""

    display_open_trades(open_trades)

    record = get_latest_record(sample_gen_trades)
    print(f"record : \n\n{pformat(record, sort_dicts=False)}\n")

    # Intialize instance of FixedExit
    fixed_exit = FixedExit()

    with pytest.raises(KeyError):
        computed_trades, computed_list = fixed_exit.close_pos(
            open_trades, record["date"], record["close"], entry_dt
        )


def test_close_pos(sample_gen_trades, open_trades):
    """Test if 'close_pos' correctly close the position with correct entry date."""

    display_open_trades(open_trades)

    record = get_latest_record(sample_gen_trades)
    print(f"record : \n\n{pformat(record, sort_dicts=False)}\n")

    # Intialize instance of FixedExit
    fixed_exit = FixedExit()
    entry_dt = datetime(2025, 4, 8)

    computed_trades, computed_list = fixed_exit.close_pos(
        open_trades, record["date"], record["close"], entry_dt
    )

    print(f"Computed trades : \n\n{pformat(computed_trades, sort_dicts=False)}\n")
    print(f"Computed list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    expected_trades = deque(
        [
            StockTrade(
                ticker="AAPL",
                entry_datetime=datetime(2025, 4, 7, tzinfo=None),
                entry_action="buy",
                entry_lots=10,
                entry_price=181.46,
            ),
            StockTrade(
                ticker="AAPL",
                entry_datetime=datetime(2025, 4, 11, tzinfo=None),
                entry_action="buy",
                entry_lots=10,
                entry_price=198.15,
            ),
        ]
    )

    expected_list = [
        {
            "ticker": "AAPL",
            "entry_datetime": datetime(2025, 4, 8, 0, 0),
            "entry_action": "buy",
            "entry_lots": Decimal("10"),
            "entry_price": Decimal("172.42"),
            "exit_datetime": datetime(2025, 4, 17, 0, 0),
            "exit_action": "sell",
            "exit_lots": Decimal("10"),
            "exit_price": Decimal("196.72"),
            "days_held": 9,
            "profit_loss": Decimal("24.30"),
            "percent_ret": Decimal("0.140935"),
            "daily_ret": Decimal("0.014758"),
            "win": 1,
        }
    ]

    print(f"Expected trades : \n\n{pformat(expected_trades, sort_dicts=False)}\n")
    print(f"Expected list : \n\n{pformat(expected_list, sort_dicts=False)}\n")

    assert computed_trades == expected_trades
    assert computed_list == expected_list
