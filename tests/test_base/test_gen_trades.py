"""Generate test for non-abstract public methods in 'GenTrades'.

- test_init
- test_exit_all
- test_exit_all_end
- test_cal_stop_price
- test_check_stop_loss
- test_take_profit
- test_check_profit
- test_trailing_profit
- test_check_trailing_profit
- test_append_info
- test_iterate_df
- test_open_new_pos
- test_open_new_pos
- test_open_trades
- test_iterate_df
"""

from collections import deque
from datetime import datetime
from pprint import pformat

import pytest

from ..test_utils import (
    cal_percentloss_stop_price,
    gen_check_profit_completed_list,
    gen_check_stop_loss_completed_list,
    gen_exit_all_end_completed_list,
    gen_exit_record,
    gen_take_profit_completed_list,
    gen_takeallexit_completed_list,
    gen_testgentrades_inst,
)


def test_init(trading_config, risk_config):
    """Test '__init__' method for 'GenTrades' class."""

    test_inst = gen_testgentrades_inst(trading_config, risk_config)

    assert test_inst.entry_struct == "MultiEntry"
    assert test_inst.exit_struct == "FIFOExit"
    assert test_inst.stop_method == "no_stop"
    assert test_inst.trail_method == "no_trail"


def test_exit_all(trading_config, risk_config, open_trades):
    """Test 'exit_all' method for 'GenTrades' class."""

    # Create test instance with updated 'open_trades' attribute
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=open_trades.copy()
    )

    # Generate completed trade list based on 'exit_dt' datetime
    exit_dt = datetime(2025, 4, 14, tzinfo=None)
    exit_price = 202.52

    # Generate computed and expected completed list
    computed_list = test_inst.exit_all(exit_dt, exit_price)
    expected_list = gen_takeallexit_completed_list(open_trades, exit_dt, exit_price)

    assert computed_list == expected_list
    assert test_inst.open_trades == deque()


def test_exit_all_end(
    trading_config, risk_config, open_trades, completed_list, sample_gen_trades
):
    """Test 'exit_all_end' method for 'GenTrades' class."""

    # OHLCV of AAPL at end of trading period i.e. last item in sample_gen_trades
    record = sample_gen_trades.iloc[-1, :].to_dict()

    # Test 1: No open positions scenario
    test_inst = gen_testgentrades_inst(trading_config, risk_config, open_trades=deque())
    computed_list = test_inst.exit_all_end(completed_list.copy(), record.copy())
    assert computed_list == completed_list

    # Test 2: open positios scenario
    test_inst.open_trades = open_trades.copy()
    computed_list = test_inst.exit_all_end(completed_list.copy(), record.copy())
    expected_list = gen_exit_all_end_completed_list(
        open_trades.copy(), completed_list.copy(), record.copy()
    )

    assert computed_list == expected_list
    assert test_inst.open_trades == deque()
    assert len(computed_list) == 4  # 3 closed + existing 1


def test_cal_stop_price(trading_config, risk_config, open_trades):
    """Test 'cal_stop_price' method for 'GenTrades' class."""

    # Create test instance with 'stop_method' == 'PercentLoss'
    test_inst = gen_testgentrades_inst(
        trading_config,
        risk_config,
        stop_method="PercentLoss",
        open_trades=open_trades.copy(),
    )

    # Calculate expected and computed stop price
    computed_price = test_inst.cal_stop_price()
    expected_price = cal_percentloss_stop_price(open_trades, risk_config.percent_loss)

    assert computed_price == expected_price


@pytest.mark.parametrize(
    "stop_method, open_trades_setup",
    [("latestLoss", "empty"), ("no_stop", "with_trades")],
)
def test_check_stop_loss_no_action(
    trading_config,
    risk_config,
    open_trades,
    completed_list,
    sample_gen_trades,
    stop_method,
    open_trades_setup,
):
    """Test scenarios where 'check_stop_loss' returns original 'completed_list'."""

    # OHLCV of AAPL at end of trading period i.e. last item in sample_gen_trades
    record = sample_gen_trades.iloc[-1, :].to_dict()

    # Set up 'open_trades'
    trades_input = deque() if open_trades_setup == "empty" else open_trades.copy()

    # Generate test instance based on 'stop_method' and 'open_trades_setup'
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=trades_input, stop_method=stop_method
    )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_stop_loss(completed_list.copy(), record.copy())

    assert computed_list == completed_list


def test_check_stop_loss_nearest_loss(
    trading_config, risk_config, open_trades, completed_list, sample_gen_trades
):
    """Test 'check_stop_loss' for 'NearestLoss' scenario."""

    # OHLCV of AAPL on 8 Apr 2025
    df = sample_gen_trades
    record = df.loc[df["date"] == "2025-04-08", :].to_dict(orient="records")[0]

    test_inst = gen_testgentrades_inst(
        trading_config,
        risk_config,
        stop_method="NearestLoss",
        open_trades=open_trades.copy(),
    )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_stop_loss(completed_list.copy(), record.copy())
    expected_list, trigger_info = gen_check_stop_loss_completed_list(
        dict(trading_cfg=trading_config, risk_cfg=risk_config),
        open_trades.copy(),
        completed_list.copy(),
        record.copy(),
        risk_config.percent_loss,
    )

    # print(f"\n\ncomputed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")
    # print(f"expected_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    assert computed_list == expected_list
    assert test_inst.stop_info_list == [trigger_info]


@pytest.mark.parametrize("exit_sig", ["wait", "buy"])
def test_take_profit_no_action(
    trading_config,
    risk_config,
    sample_gen_trades,
    exit_sig,
):
    """Test scenarios where 'take_profit' returns empty list."""

    # Generate record with desired 'exit_signal'
    record = gen_exit_record(sample_gen_trades, exit_sig)
    dt = record["date"]
    ex_sig = record["exit_signal"]
    exit_price = record["close"]  # Assume position closed at closing

    # Generate generic test instance
    test_inst = gen_testgentrades_inst(trading_config, risk_config)

    # Generate computed 'completed_list'
    computed_list = test_inst.take_profit(dt, ex_sig, exit_price)

    assert computed_list == []


def test_take_profit_fifoexit(
    trading_config, risk_config, open_trades, sample_gen_trades
):
    """Test 'take_profit' for 'FIFOExit' scenario."""

    # OHLCV of AAPL on 10 Apr 2025 (sell signal)
    df = sample_gen_trades
    record = df.loc[df["date"] == "2025-04-10", :].to_dict(orient="records")[0]

    dt = record["date"]
    ex_sig = record["exit_signal"]
    exit_price = record["close"]  # Assume position closed at closing

    # Generate test instance with 'exit_method' == 'FIFOExit'
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=open_trades.copy()
    )

    # Generate computed and expected 'completed_list'
    computed_list = test_inst.take_profit(dt, ex_sig, exit_price)
    expected_open_trades, expected_list = gen_take_profit_completed_list(
        open_trades.copy(), dt, exit_price
    )

    assert computed_list == expected_list
    assert test_inst.open_trades == expected_open_trades


@pytest.mark.parametrize(
    "exit_sig, open_trades_setup",
    [("wait", "with_trades"), ("sell", "empty")],
)
def test_check_profit_no_action(
    trading_config,
    risk_config,
    open_trades,
    completed_list,
    sample_gen_trades,
    exit_sig,
    open_trades_setup,
):
    """Test scenarios where 'check_profit' returns original 'completed_list'."""

    # Generate record with required exe
    record = gen_exit_record(sample_gen_trades, exit_sig)

    # Set up 'open_trades'
    trades_input = deque() if open_trades_setup == "empty" else open_trades.copy()

    # Generate test instance based on 'stop_method' and 'open_trades_setup'
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=trades_input
    )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_profit(completed_list.copy(), record.copy())

    assert computed_list == completed_list


def test_check_profit_fifoexit(
    trading_config, risk_config, open_trades, completed_list, sample_gen_trades
):
    """Test 'check_profit' for 'FIFOExit' scenario."""

    # Get the latest record with 'sell' exit signal
    df = sample_gen_trades
    record = df.loc[df["exit_signal"] == "sell", :].tail(1).to_dict(orient="records")[0]

    test_inst = gen_testgentrades_inst(
        trading_config,
        risk_config,
        open_trades=open_trades.copy(),
    )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_profit(completed_list.copy(), record.copy())
    expected_trades, expected_list = gen_check_profit_completed_list(
        open_trades.copy(),
        completed_list.copy(),
        record.copy(),
    )

    # print(f"\n\ncomputed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")
    # print(f"expected_list : \n\n{pformat(expected_list, sort_dicts=False)}\n")
    # print(f"expected_trades : \n\n{pformat(expected_trades, sort_dicts=False)}\n")
    # print(f"test_inst.open_trades : \n\n{pformat(test_inst.open_trades)}\n")

    assert computed_list == expected_list
    assert test_inst.open_trades == expected_trades
