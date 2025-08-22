"""Generate test for 'HalfFIFOExit' method."""

import math
from collections import deque
from pprint import pformat

import pytest

from strat_backtest.exit_method import HalfFIFOExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_halfexit_utils import (
    gen_half_fifo_closedpositionresult,
    update_open_trades,
)
from tests.utils.test_utils import get_completed_lots, get_latest_record, get_open_lots


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

        assert get_open_lots(open_trades) == math.floor(open_lots / 2)
        assert get_completed_lots(computed_list) == math.ceil(open_lots / 2)
        i += 1


def test_half_fifoexit_no_action(sample_gen_trades):
    """Test if 'close_pos' method of 'FIFOExit' return empty deque list if empty"""

    record = get_latest_record(sample_gen_trades)

    half_fifo_exit = HalfFIFOExit()
    computed_trades, computed_list = half_fifo_exit.close_pos(
        deque(), record["date"], record["open"]
    )

    assert computed_trades == deque()
    assert computed_list == []


@pytest.mark.parametrize(
    "is_partial, entry_lots_list",
    [
        (False, [10, 3, 2]),
        (False, [2, 3, 10]),
        (False, [3, 10, 2]),
        (True, [10, 3, 2]),
        (True, [6, 3, 10]),
        (True, [6, 10, 2]),
    ],
)
def test_half_fifoexit(open_trades, sample_gen_trades, is_partial, entry_lots_list):
    """Test if 'close_pos' method of 'FIFOExit' correctly closed first open position."""

    record = get_latest_record(sample_gen_trades)

    # Update 'open_trades' based on 'is_partial' and 'entry_lots_list'
    open_trades = update_open_trades(
        open_trades, entry_lots_list, is_partial, is_fifo=True
    )

    # print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    print("\n\n")
    display_open_trades(open_trades)

    half_fifo_exit = HalfFIFOExit()
    computed_trades, computed_list = half_fifo_exit.close_pos(
        open_trades.copy(), record["date"], record["open"]
    )

    display_open_trades(computed_trades, "computed_trades")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    # Compute expected open trades by removing half of the earliest existing open position
    expected_trades, expected_list = gen_half_fifo_closedpositionresult(
        open_trades.copy(), record.copy()
    )

    display_open_trades(expected_trades, "expected_trades")
    print(f"expected_list : \n\n{pformat(expected_list, sort_dicts=False)}\n")

    assert computed_trades == expected_trades
    assert computed_list == expected_list
