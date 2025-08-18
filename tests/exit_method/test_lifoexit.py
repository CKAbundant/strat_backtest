"""Generate test for 'LIFOExit' method.'"""

from collections import deque
from pprint import pformat

from strat_backtest.exit_method import LIFOExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import get_latest_record, update_open_pos


def test_lifoexit_no_action(sample_gen_trades):
    """Test if 'close_pos' method of 'FIFOExit' return empty deque list if empty"""

    record = get_latest_record(sample_gen_trades)

    lifo_exit = LIFOExit()
    computed_trades, computed_list = lifo_exit.close_pos(
        deque(), record["date"], record["open"]
    )

    assert computed_trades == deque()
    assert computed_list == []


def test_lifoexit(open_trades, sample_gen_trades):
    """Test if 'close_pos' method of 'LIFOExit' correctly closed first open position."""

    record = get_latest_record(sample_gen_trades)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    fifo_exit = LIFOExit()
    computed_trades, computed_list = fifo_exit.close_pos(
        open_trades.copy(), record["date"], record["open"]
    )

    expected_trades = open_trades.copy()

    # Pop first entry and update exit price and datetime
    completed_trade = expected_trades.pop()
    completed_trade = update_open_pos(completed_trade, record["date"], record["open"])
    expected_list = [completed_trade.model_dump()]

    display_open_trades(computed_trades, "computed_trades")
    display_open_trades(expected_trades, "expected_trades")

    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")
    print(f"expected_list : \n\n{pformat(expected_list, sort_dicts=False)}\n")

    assert computed_trades == expected_trades
    assert computed_list == expected_list
