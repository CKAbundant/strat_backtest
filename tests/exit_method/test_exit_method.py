"""Generate test for concrete implementation of 'ExitStruct' except for 'FixedExit'."""

from pprint import pformat

import pytest

from strat_backtest.exit_method import FIFOExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import get_latest_record


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
    """Test if return ValueError for negative lots or exit lots > entry_lots."""

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
