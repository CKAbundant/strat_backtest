"""Generate test for 'HalfFIFOExit' method."""

import math
from collections import deque
from pprint import pformat

from strat_backtest.exit_method import HalfFIFOExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import (
    get_completed_lots,
    get_latest_record,
    get_open_lots,
    update_open_pos,
)


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


def test_half_fifoexit(open_trades, sample_gen_trades):
    """Test if 'close_pos' method of 'FIFOExit' correctly closed first open position."""

    record = get_latest_record(sample_gen_trades)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    half_fifo_exit = HalfFIFOExit()
    computed_trades, computed_list = half_fifo_exit.close_pos(
        open_trades.copy(), record["date"], record["open"]
    )

    display_open_trades(computed_trades, "computed_trades")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    # Compute expected open trades by removing half of the earliest existing open position
    total_open = get_open_lots(open_trades)
    half_completed = math.ceil(total_open / 2)

    expected_list = []
    expected_trades = deque()
    for trade in open_trades.copy():
        open_lots = trade.entry_lots - trade.exit_lots

        if half_completed <= 0:
            # Existing position is reduced by half hence append remaining trades
            # as open positions
            expected_trades.append(trade)
            continue

        if open_lots <= half_completed:
            # Number of lots is less than required half position hence
            # close off current trade
            completed_trade = update_open_pos(
                trade.model_copy(), record["date"], record["open"]
            )
            expected_list.append(completed_trade.model_dump())

            # Reduce required lots by open lots in current trade
            half_completed -= open_lots

        else:
            # Close open position by 'half_position' as number of open lots
            # more than required half position. Ensure entry lots equal exit lots.
            completed_trade = update_open_pos(
                trade.model_copy(),
                record["date"],
                record["open"],
                exit_lots=half_completed,
            )
            completed_trade.entry_lots = completed_trade.exit_lots

            # Update trade to reflect partal close
            open_trade = update_open_pos(
                trade.model_copy(),
                record["date"],
                record["open"],
                exit_lots=trade.exit_lots + half_completed,
            )

            expected_list.append(completed_trade.model_dump())
            expected_trades.append(open_trade)
            half_completed = 0

    display_open_trades(expected_trades, "expected_trades")
    print(f"expected_list : \n\n{pformat(expected_list, sort_dicts=False)}\n")

    # assert computed_trades == expected_trades
