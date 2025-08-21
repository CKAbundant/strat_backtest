"""Generate test for 'TakeAllExit' method."""

from collections import deque
from decimal import Decimal
from pprint import pformat

import pytest

from strat_backtest.exit_method import TakeAllExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_takeallexit_utils import update_open_trades
from tests.utils.test_utils import get_latest_record


def test_takeallexit_no_action(sample_gen_trades):
    """Test if 'close_pos' return empty open trades and completed list when
    no open positions."""

    record = get_latest_record(sample_gen_trades)

    take_all_exit = TakeAllExit()
    computed_trades, computed_list = take_all_exit.close_pos(
        deque(), record["date"], record["close"]
    )

    assert computed_trades == deque()
    assert computed_list == []


@pytest.mark.parametrize(
    "exit_lots_list",
    [
        (0, 0, 0),
        (2, 4, 6),
        (0, 4, 6),
        (2, 0, 6),
        (2, 4, 0),
        (7, 0, 0),
        (0, 1, 0),
        (0, 0, 5),
    ],
)
def test_takeallexit(open_trades, sample_gen_trades, exit_lots_list):
    """Test if 'close_pos' method closes all open positions correctly."""

    record = get_latest_record(sample_gen_trades)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    updated_trades = update_open_trades(open_trades, exit_lots_list)
    display_open_trades(updated_trades, "updated_trades")

    take_all_exit = TakeAllExit()
    computed_trades, computed_list = take_all_exit.close_pos(
        updated_trades.copy(), record["date"], record["close"]
    )

    display_open_trades(computed_trades, "computed_trades")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    assert computed_trades == deque()
    assert [trade.get("exit_lots") for trade in computed_list] == [
        Decimal("10") - exit_lots for exit_lots in exit_lots_list
    ]
