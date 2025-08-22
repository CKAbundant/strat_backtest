"""Generate test for 'FIFOExit' method."""

from collections import deque
from pprint import pformat

import pytest

from strat_backtest.exit_method import FIFOExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import get_latest_record, update_open_pos


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


def test_fifoexit_no_action(sample_gen_trades):
    """Test if 'close_pos' method of 'FIFOExit' return empty deque list if empty"""

    record = get_latest_record(sample_gen_trades)

    fifo_exit = FIFOExit()
    computed_trades, computed_list = fifo_exit.close_pos(
        deque(), record["date"], record["open"]
    )

    assert computed_trades == deque()
    assert computed_list == []


def test_fifoexit(open_trades, sample_gen_trades):
    """Test if 'close_pos' method of 'FIFOExit' correctly closed first open position."""

    record = get_latest_record(sample_gen_trades)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    fifo_exit = FIFOExit()
    computed_trades, computed_list = fifo_exit.close_pos(
        open_trades.copy(), record["date"], record["open"]
    )

    expected_trades = open_trades.copy()

    # Pop first entry and update exit price and datetime
    completed_trade = expected_trades.popleft()
    completed_trade = update_open_pos(completed_trade, record["date"], record["open"])
    expected_list = [completed_trade.model_dump()]

    display_open_trades(computed_trades, "computed_trades")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    assert computed_trades == expected_trades
    assert computed_list == expected_list
