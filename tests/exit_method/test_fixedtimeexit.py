"""Generate test for 'FixedTimeExit' method."""

from collections import deque
from datetime import datetime, timedelta
from pprint import pformat

import pytest

from strat_backtest.exit_method.fixed_time_exit import FixedTimeExit
from strat_backtest.utils.utils import display_open_trades
from tests.utils.test_utils import get_latest_record


@pytest.mark.parametrize("time_period", [1, 3, 5, 10])
def test_init_valid_time_period(time_period):
    """Test if FixedTimeExit initializes correctly with valid time periods."""
    exit_method = FixedTimeExit(time_period)
    assert exit_method.time_period == time_period


@pytest.mark.parametrize("invalid_time_period", [0, -1, -5])
def test_init_invalid_time_period(invalid_time_period):
    """Test if FixedTimeExit raises ValueError for invalid time periods."""
    with pytest.raises(ValueError, match="time_period must be a positive integer"):
        FixedTimeExit(invalid_time_period)


def test_fixed_time_exit_no_action(sample_gen_trades):
    """Test if 'close_pos' method of 'FixedTimeExit' returns empty deque list if empty."""
    record = get_latest_record(sample_gen_trades)

    fixed_time_exit = FixedTimeExit()
    computed_trades, computed_list = fixed_time_exit.close_pos(
        deque(), record["date"], record["open"]
    )

    assert computed_trades == deque()
    assert computed_list == []


def test_fixed_time_exit_no_expired_positions(open_trades, sample_gen_trades):
    """Test if 'close_pos' method returns unchanged trades when no positions have expired."""
    record = get_latest_record(sample_gen_trades)

    # Set time period to a large value so no positions expire
    fixed_time_exit = FixedTimeExit(time_period=100)
    computed_trades, computed_list = fixed_time_exit.close_pos(
        open_trades.copy(), record["date"], record["open"]
    )

    assert computed_trades == open_trades
    assert computed_list == []


def test_fixed_time_exit_all_positions_expired(open_trades, sample_gen_trades):
    """Test if 'close_pos' method closes all positions when all have expired."""
    record = get_latest_record(sample_gen_trades)

    # Create exit method with 1-day time period
    fixed_time_exit = FixedTimeExit(time_period=1)

    # Modify open trades to have old entry dates (2+ days ago)
    modified_trades = deque()
    old_date = record["date"] - timedelta(days=2)

    for trade in open_trades:
        modified_trade = trade.model_copy()
        modified_trade.entry_datetime = old_date
        modified_trades.append(modified_trade)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(modified_trades, "modified_trades (old entry dates)")

    computed_trades, computed_list = fixed_time_exit.close_pos(
        modified_trades, record["date"], record["open"]
    )

    display_open_trades(computed_trades, "computed_trades")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    # All positions should be closed
    assert len(computed_trades) == 0
    assert len(computed_list) == len(open_trades)


def test_fixed_time_exit_partial_expiry(open_trades, sample_gen_trades):
    """Test if 'close_pos' method closes only expired positions."""
    record = get_latest_record(sample_gen_trades)

    # Create exit method with 2-day time period
    fixed_time_exit = FixedTimeExit(time_period=2)

    # Create mixed trades: some old (3+ days) and some recent (1 day)
    modified_trades = deque()
    old_date = record["date"] - timedelta(days=3)  # Expired
    recent_date = record["date"] - timedelta(days=1)  # Not expired

    # Make first half of trades old (expired)
    expired_count = len(open_trades) // 2

    for i, trade in enumerate(open_trades):
        modified_trade = trade.model_copy()
        if i < expired_count:
            modified_trade.entry_datetime = old_date  # Will expire
        else:
            modified_trade.entry_datetime = recent_date  # Won't expire
        modified_trades.append(modified_trade)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(modified_trades, "modified_trades (mixed dates)")

    computed_trades, computed_list = fixed_time_exit.close_pos(
        modified_trades, record["date"], record["open"]
    )

    display_open_trades(computed_trades, "computed_trades")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    # Only expired positions should be closed
    expected_remaining = len(open_trades) - expired_count
    assert len(computed_trades) == expected_remaining
    assert len(computed_list) == expired_count


def test_fixed_time_exit_exact_time_boundary(open_trades, sample_gen_trades):
    """Test if 'close_pos' method handles exact time boundary correctly."""
    record = get_latest_record(sample_gen_trades)

    # Create exit method with 2-day time period
    fixed_time_exit = FixedTimeExit(time_period=2)

    # Set entry date exactly 2 days ago (should expire)
    modified_trades = deque()
    boundary_date = record["date"] - timedelta(days=2)

    for trade in open_trades:
        modified_trade = trade.model_copy()
        modified_trade.entry_datetime = boundary_date
        modified_trades.append(modified_trade)

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(modified_trades, "modified_trades (boundary dates)")

    computed_trades, computed_list = fixed_time_exit.close_pos(
        modified_trades, record["date"], record["open"]
    )

    display_open_trades(computed_trades, "computed_trades")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    # All positions should be closed (>= time_period)
    assert len(computed_trades) == 0
    assert len(computed_list) == len(open_trades)


@pytest.mark.parametrize("exit_lots", [None, 1, 5, 10])
def test_update_pos(open_trades, sample_gen_trades, exit_lots):
    """Test if '_update_pos' updates position correctly."""
    fixed_time_exit = FixedTimeExit()
    trade = open_trades[-1]
    record = get_latest_record(sample_gen_trades)
    computed_trade = fixed_time_exit._update_pos(
        trade, record["date"], record["close"], exit_lots
    )

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)
    print(f"computed_trade : \n\n{computed_trade}\n")

    expected_lots = trade.entry_lots if exit_lots is None else exit_lots

    assert computed_trade.exit_lots == expected_lots
    assert computed_trade.exit_datetime == record["date"]
    assert computed_trade.exit_price == record["close"]
