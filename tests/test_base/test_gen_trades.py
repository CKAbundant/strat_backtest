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

from ..test_utils import (
    cal_nearestloss_stop_price,
    cal_percentloss_stop_price,
    gen_check_stop_loss_completed_list,
    gen_exit_all_end_completed_list,
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


def test_exit_all_end(trading_config, risk_config, open_trades, completed_list):
    """Test 'exit_all_end' method for 'GenTrades' class."""

    # OHLCV of AAPL on 14 Apr 2025
    record = {"date": datetime(2025, 4, 14, tzinfo=None), "close": 202.52}

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


def test_check_stop_loss(trading_config, risk_config, open_trades, completed_list):
    """Test 'check_stop_loss' method for 'GenTrades' class."""

    # OHLCV of AAPL on 14 Apr 2025
    record = {
        "date": datetime(2025, 4, 8, tzinfo=None),
        "high": 190.09,
        "low": 168.99,
        "close": 172.19,
    }

    # Test 1: No open positions scenario
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=deque(), stop_method="LatestLoss"
    )
    no_open_list = test_inst.check_stop_loss(completed_list.copy(), record.copy())

    # Test 2: No 'stop_method' == 'no_stop' scenario
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=open_trades.copy()
    )
    no_stop_list = test_inst.check_stop_loss(completed_list.copy(), record.copy())

    assert no_open_list == completed_list
    assert no_stop_list == completed_list

    # Test 3: 'stop_method' == 'NearestLoss'
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

    # print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")
    # print(f"expected_list : \n\n{pformat(expected_list, sort_dicts=False)}\n")

    assert computed_list == expected_list
