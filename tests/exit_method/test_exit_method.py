"""Generate test for concrete implementation of 'ExitStruct' except for 'FixedExit'."""

import math
from pprint import pformat

import pytest

from strat_backtest.exit_method import FIFOExit, HalfFIFOExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import get_completed_lots, get_latest_record, get_open_lots


@pytest.mark.parametrize("exit_lots", [None, 1, 5, 10])
def test_update_pos(open_trades, sample_gen_trades, exit_lots):
    """Test if '_update_pos' updates position correctly."""

    fifo_exit = FIFOExit()
    trade = open_trades[-1]
    record = get_latest_record(sample_gen_trades)
    computed_trade = fifo_exit._update_pos(
        trade, record["date"], record["close"], exit_lots
    )

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)
    print(f"computed_trade : \n\n{computed_trade}\n")

    expected_lots = trade.entry_lots if exit_lots is None else exit_lots

    assert computed_trade.exit_lots == expected_lots
    assert computed_trade.exit_datetime == record["date"]
    assert computed_trade.exit_price == record["close"]


@pytest.mark.parametrize(
    "exit_lots, exc_msg",
    [
        (-10, "Exit lots (-10) cannot be negative"),
        (20, "Exit lots (20) are more than entry lots (10)"),
    ],
)
def test_validate_exit_lots(open_trades, sample_gen_trades, exit_lots, exc_msg):
    """Test if '_validate_exit_lots' return ValueError for negative lots
    or exit lots > entry_lots."""

    fifo_exit = FIFOExit()
    trade = open_trades[-1]
    record = get_latest_record(sample_gen_trades)

    with pytest.raises(ValueError) as exc_info:
        computed_trade = fifo_exit._update_pos(
            trade, record["date"], record["close"], exit_lots
        )

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    print(f"exception : {exc_info.value}")
    assert exc_msg == str(exc_info.value)


def test_update_half_status(open_trades, sample_gen_trades):
    """Test if '_update_half_status' reduce open positions by half recursively.'"""

    record = get_latest_record(sample_gen_trades)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    half_fifo_exit = HalfFIFOExit()
    i = 1

    while (open_lots := get_open_lots(open_trades)) > 0:
        open_trades, computed_list = half_fifo_exit._update_half_status(
            open_trades, record["date"], record["open"]
        )
        print(f"\n\nround : {i}")
        display_open_trades(open_trades, "computed_trades")
        print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")
        print(f"{math.floor(open_lots/2)=}")

        assert get_open_lots(open_trades) == math.floor(open_lots / 2)
        assert get_completed_lots(computed_list) == math.ceil(open_lots / 2)
        i += 1
