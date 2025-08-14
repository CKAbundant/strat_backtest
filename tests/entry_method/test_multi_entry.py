"""Test entry strategies.

- Multi entry -> multiple positions allowed
- Single entry -> new position created only when no existing position
- Multi half entry -> number of new positions = half of existing positions
"""

from datetime import datetime
from pprint import pformat

import pytest

from strat_backtest.entry_method import MultiEntry, MultiHalfEntry, SingleEntry
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import get_latest_record


@pytest.mark.parametrize("num_lots", [10])
def test_multientry(open_trades, sample_gen_trades, num_lots):
    """Check if new position created even if there are existing open positions."""

    record = get_latest_record(sample_gen_trades)
    print(f"record : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    # multi_entry = MultiEntry(num_lots=num_lots)
    # multi_entry.open_new_pos(
    #     open_trades,
    #     "AAPL",
    #     record["date"],
    # )
