"""Test entry strategies.

- Multi entry -> multiple positions allowed
- Single entry -> new position created only when no existing position
- Multi half entry -> number of new positions = half of existing positions
"""

from datetime import datetime
from pprint import pformat

import pandas.testing as pdt
import pytest
from pydantic import ValidationError

from strat_backtest.entry_method import MultiEntry, MultiHalfEntry, SingleEntry
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import create_new_pos, get_latest_record


def test_multientry(
    open_trades,
    sample_gen_trades,
):
    """Check if new position created even if there are existing open positions."""

    num_lots = 10
    record = get_latest_record(sample_gen_trades)
    print(f"record : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)

    multi_entry = MultiEntry(num_lots=num_lots)
    computed_trades = multi_entry.open_new_pos(
        open_trades.copy(),
        "AAPL",
        record["date"],
        record["entry_signal"],
        record["open"],
    )

    expected_trades = create_new_pos(record, num_lots, open_trades.copy())
    display_open_trades(computed_trades, "computed_trades")

    assert computed_trades == expected_trades


@pytest.mark.parametrize(
    "ticker, date, entry_signal, exc_msg",
    [
        (
            "MSFT",
            "2025-4-17",
            "buy",
            "'MSFT' is different from ticker used in 'open_trades' i.e. 'AAPL'",
        ),
        (
            "AAPL",
            "2025-4-1",
            "buy",
            "Entry datetime '2025-04-01' is earlier than latest entry datetime '2025-04-11'",
        ),
        (
            "AAPL",
            "2025-4-17",
            "sell",
            "Entry action 'sell' is different from entry action used in 'open_trades' i.e. 'buy'",
        ),
    ],
)
def test_error_entry(open_trades, ticker, date, entry_signal, exc_msg):
    """Check if ValueError is raised for inconsistent ticker, entry and date (entry
    date earlier than existing open trades)."""

    display_open_trades(open_trades)

    multi_entry = MultiEntry(num_lots=10)

    with pytest.raises(ValueError) as exc_info:
        computed_trades = multi_entry.open_new_pos(
            open_trades.copy(), ticker, date, entry_signal, 200
        )

    print(f"\n{str(exc_info.value)}\n")
    assert exc_msg == str(exc_info.value)
