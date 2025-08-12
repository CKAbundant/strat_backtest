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
- test_open_new_pos
- test_append_info
- test_iterate_df
"""

from collections import deque
from datetime import datetime
from pprint import pformat

import pandas as pd
import pandas.testing as pdt
import pytest

from strat_backtest.utils.pos_utils import get_std_field
from strat_backtest.utils.utils import display_open_trades
from tests.test_fixedexit_utils import gen_test_df
from tests.test_utils import (
    cal_percentloss_stop_price,
    cal_trailing_price,
    create_new_pos,
    gen_check_profit_completed_list,
    gen_check_stop_loss_completed_list,
    gen_check_trailing_profit_completed_list,
    gen_exit_all_end_completed_list,
    gen_record,
    gen_take_profit_completed_list,
    gen_takeallexit_completed_list,
    gen_testgentrades_inst,
    get_date_record,
    get_latest_record,
    init_flip,
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

    # Get latest record in sample DataFrame
    record = get_latest_record(sample_gen_trades)
    print(f"\n\nrecord : \n\n{record}\n")
    display_open_trades(open_trades)

    # Test 1: No open positions scenario
    test_inst = gen_testgentrades_inst(
        trading_config,
        risk_config,
        open_trades=deque(),
    )
    computed_list = test_inst.exit_all_end(completed_list.copy(), record.copy())

    assert computed_list == completed_list

    # Test 2: open positios scenario
    test_inst.open_trades = open_trades.copy()
    computed_list = test_inst.exit_all_end(completed_list.copy(), record.copy())
    expected_list = gen_exit_all_end_completed_list(
        open_trades.copy(), completed_list.copy(), record.copy(), "close"
    )

    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

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

    print(f"{computed_price=}")

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

    # Get latest record in sample DataFrame
    record = get_latest_record(sample_gen_trades)

    # Set up 'open_trades'
    trades_input = deque() if open_trades_setup == "empty" else open_trades.copy()

    # Generate test instance based on 'stop_method' and 'open_trades_setup'
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=trades_input, stop_method=stop_method
    )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_stop_loss(completed_list.copy(), record.copy())

    assert computed_list == completed_list


def test_check_stop_loss_nearestloss(
    trading_config, risk_config, open_trades, completed_list, sample_gen_trades
):
    """Test 'check_stop_loss' for 'NearestLoss' scenario."""

    percent_loss = 0.01

    # OHLCV of AAPL on 15 Apr 2025
    record = get_date_record(sample_gen_trades, "2025-04-16")

    # Generate test instance with 'stop_method' == 'NearestLoss'
    params = {
        "trading_cfg": trading_config,
        "risk_cfg": risk_config,
        "stop_method": "NearestLoss",
        "percent_loss": percent_loss,
        "open_trades": open_trades.copy(),
    }
    test_inst = gen_testgentrades_inst(**params)

    # Generate computed 'completed_list'
    computed_list = test_inst.check_stop_loss(completed_list.copy(), record.copy())

    # Compute expected 'completed_list'
    params["open_trades"] = open_trades.copy()
    expected_list, trigger_info = gen_check_stop_loss_completed_list(
        params,
        completed_list.copy(),
        record.copy(),
    )
    expected_stop_info_list = [trigger_info] if trigger_info else []

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)
    print(f"{198.15*(1-percent_loss)=}")
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

    assert computed_list == expected_list
    assert test_inst.stop_info_list == expected_stop_info_list


@pytest.mark.parametrize("exit_sig", ["wait", "buy"])
def test_take_profit_no_action(
    trading_config,
    risk_config,
    sample_gen_trades,
    exit_sig,
):
    """Test scenarios where 'take_profit' returns empty list."""

    # Generate record with desired 'exit_signal'
    record = gen_record(sample_gen_trades, exit_signal=exit_sig)

    dt = record["date"]
    exit_signal = record["exit_signal"]
    exit_price = record["close"]  # Assume position closed at closing

    # Generate generic test instance
    test_inst = gen_testgentrades_inst(trading_config, risk_config)

    # Generate computed 'completed_list'
    computed_list = test_inst.take_profit(dt, exit_signal, exit_price)

    assert computed_list == []


def test_take_profit_fifoexit(
    trading_config, risk_config, open_trades, sample_gen_trades
):
    """Test 'take_profit' for 'FIFOExit' scenario."""

    # OHLCV of AAPL on 15 Apr 2025 (sell signal)
    record = get_date_record(sample_gen_trades, "2025-04-15")

    dt = record["date"]
    exit_signal = record["exit_signal"]
    exit_price = record["close"]  # Assume position closed at closing

    # Generate test instance with 'exit_method' == 'FIFOExit'
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=open_trades.copy()
    )

    # Generate computed and expected 'completed_list'
    computed_list = test_inst.take_profit(dt, exit_signal, exit_price)
    expected_open_trades, expected_list = gen_take_profit_completed_list(
        open_trades.copy(), dt, exit_price
    )

    print(f"\n\nrecord : \n\n{pformat(record, sort_dicts=False)}\n")
    display_open_trades(open_trades)
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")

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

    # Generate record with required exit signal
    record = gen_record(sample_gen_trades, exit_signal=exit_sig)

    # Set up 'open_trades'
    trades_input = deque() if open_trades_setup == "empty" else open_trades.copy()

    # Generate test instance based on 'stop_method' and 'open_trades_setup'
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=trades_input
    )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_profit(completed_list.copy(), record.copy())

    assert computed_list == completed_list


@pytest.mark.parametrize("entry_sig, exit_sig", [("sell", "sell"), ("buy", "sell")])
# @pytest.mark.parametrize("entry_sig, exit_sig", [("sell", "sell")])
def test_check_profit_fifoexit(
    trading_config,
    risk_config,
    open_trades,
    completed_list,
    sample_gen_trades,
    entry_sig,
    exit_sig,
):
    """Test 'check_profit' for 'FIFOExit' scenario."""

    # Get the latest 2 records to ensure exit date will always be later than
    # entry date for open positions
    prev_record, latest_record = sample_gen_trades.iloc[-2:, :].to_dict(
        orient="records"
    )

    # Generate instance of 'GenTradesTest' for testing
    test_inst = gen_testgentrades_inst(
        trading_config,
        risk_config,
        open_trades=open_trades.copy(),
    )

    if entry_sig == exit_sig:
        # Flip position in entry and exit signals are the same
        test_inst = init_flip(test_inst, prev_record, entry_sig, exit_sig)

        expected_list = gen_exit_all_end_completed_list(
            open_trades.copy(), completed_list.copy(), latest_record.copy(), "open"
        )
        expected_trades = deque()

    else:
        # Update 'records' attribute in order to qualify for trade exit
        test_inst.inst_cache["sig_ex_eval"].records = [prev_record]
        expected_trades, expected_list = gen_check_profit_completed_list(
            open_trades.copy(),
            completed_list.copy(),
            latest_record.copy(),
        )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_profit(completed_list.copy(), latest_record.copy())

    print(f"\n\nlatest_records : \n\n{pformat(latest_record, sort_dicts=False)}\n")
    display_open_trades(open_trades)
    print(f"computed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")
    print(
        f"\n\ntest_inst.open_trades : \n\n{pformat(test_inst.open_trades, sort_dicts=False)}\n"
    )

    assert computed_list == expected_list
    assert test_inst.open_trades == expected_trades


@pytest.mark.parametrize("step", [None, 0.01])
def test_cal_trailing_profit(
    trading_config, risk_config, open_trades, sample_gen_trades, step
):
    """Test 'cal_trailing_profit' method for 'FirstTrail' trailing method."""

    # Get latest record in sample DataFrame
    record = get_latest_record(sample_gen_trades)

    # Create test instance with 'trail_method' == 'PercentLoss'
    test_inst = gen_testgentrades_inst(
        trading_config,
        risk_config,
        open_trades=open_trades.copy(),
        trail_method="FirstTrail",
        step=step,
    )

    # Calculate expected and computed stop price
    computed_price = test_inst.cal_trailing_profit(record.copy())
    expected_price = cal_trailing_price(
        open_trades.copy(), record.copy(), test_inst.trigger_trail, test_inst.step
    )

    assert computed_price == expected_price


@pytest.mark.parametrize(
    "trail_method, open_trades_setup",
    [("FirstTrail", "empty"), ("no_trail", "with_trades")],
)
def test_check_trailing_profit_no_action(
    trading_config,
    risk_config,
    open_trades,
    completed_list,
    sample_gen_trades,
    trail_method,
    open_trades_setup,
):
    """Test scenarios where 'check_stop_loss' returns original 'completed_list'."""

    # Get latest record in sample DataFrame
    record = get_latest_record(sample_gen_trades)

    # Set up 'open_trades'
    trades_input = deque() if open_trades_setup == "empty" else open_trades.copy()

    # Generate test instance based on 'stop_method' and 'open_trades_setup'
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=trades_input, trail_method=trail_method
    )

    # Generate computed 'completed_list'
    computed_list = test_inst.check_stop_loss(completed_list.copy(), record.copy())

    assert computed_list == completed_list


@pytest.mark.parametrize("trigger_trail", [0.5, 0.01])
def test_check_trailing_profit_firsttrail(
    trading_config,
    risk_config,
    open_trades,
    completed_list,
    sample_gen_trades,
    trigger_trail,
):
    """Test 'check_stop_loss' for 'NearestLoss' scenario."""

    # Get latest record in sample DataFrame
    record = get_latest_record(sample_gen_trades)

    # Generate test instance with 'trail_method' == 'FirstTrail'
    params = {
        "trading_cfg": trading_config,
        "risk_cfg": risk_config,
        "trail_method": "FirstTrail",
        "trigger_trail": trigger_trail,
        "open_trades": open_trades.copy(),
    }
    test_inst = gen_testgentrades_inst(**params)

    # Generate computed 'completed_list'
    computed_list = test_inst.check_trailing_profit(
        completed_list.copy(), record.copy()
    )

    # Ensure 'open_trades' is correctly parsed in params
    params["open_trades"] = open_trades.copy()

    expected_list, trigger_info = gen_check_trailing_profit_completed_list(
        params,
        completed_list.copy(),
        record.copy(),
    )
    expected_trail_info_list = [trigger_info] if trigger_info else []

    # print(f"\n\ncomputed_list : \n\n{pformat(computed_list, sort_dicts=False)}\n")
    # print(f"expected_list : \n\n{pformat(expected_list, sort_dicts=False)}\n")
    # print(f"{expected_trail_info_list=}")

    assert computed_list == expected_list
    assert test_inst.trail_info_list == expected_trail_info_list


@pytest.mark.parametrize("sig_evaluator", ["OpenEvaluator", "BreakoutEvaluator"])
def test_open_new_pos_no_action(
    trading_config, risk_config, sample_gen_trades, sig_evaluator
):
    """Test 'open_new_pos' for no action scenario."""

    # Set 'entry_signal' to 'wait' in record
    record = gen_record(sample_gen_trades, entry_signal="wait")

    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, sig_eval_method=sig_evaluator
    )
    test_inst.check_new_pos(record["ticker"], record.copy())

    assert not test_inst.open_trades


def test_open_new_pos_multientry(
    trading_config, risk_config, open_trades, sample_gen_trades
):
    """Test 'open_new_pos' for multiple entry."""

    display_open_trades(open_trades)

    # Get the latest 2 records to ensure exit date will always be later than
    # entry date for open positions
    prev_record, latest_record = sample_gen_trades.iloc[-2:, :].to_dict(
        orient="records"
    )

    # Set 'entry_signal' for 'prev_record' based on 'open_trades'
    entry_action = get_std_field(open_trades, "entry_action")
    prev_record["entry_signal"] = "buy"

    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, open_trades=open_trades.copy()
    )

    # Update 'records' with 'prev_record' to ensure trade confirmation
    test_inst.inst_cache["sig_ent_eval"].records = [prev_record]
    test_inst.check_new_pos(latest_record["ticker"], latest_record.copy())
    display_open_trades(test_inst.open_trades)

    expected_trades = create_new_pos(
        latest_record, trading_config.num_lots, open_trades.copy()
    )
    print("expected trades :")
    display_open_trades(expected_trades)

    assert test_inst.open_trades == expected_trades


def test_append_info(trading_config, risk_config, sample_gen_trades, stop_info_list):
    """Test 'append_info' method in 'GenTrades'."""

    test_inst = gen_testgentrades_inst(trading_config, risk_config)

    # Generate computed DataFrame after appending
    computed_df = test_inst.append_info(sample_gen_trades, stop_info_list)

    # Generate expected DataFrame after appending
    df_stop = pd.DataFrame(stop_info_list)
    expected_df = pd.merge(sample_gen_trades, df_stop, on="date", how="left")

    pdt.assert_frame_equal(computed_df, expected_df)


@pytest.mark.parametrize(
    "sig_evaluator, parquet_path",
    [
        ("OpenEvaluator", "open_eval_trades.parquet"),
        ("BreakoutEvaluator", "breakout_eval_trades.parquet"),
    ],
)
def test_iterate_df(
    trading_config, risk_config, sample_gen_trades, sig_evaluator, parquet_path
):
    """Test 'iterate_df' method in 'GenTrades'."""

    print(f"\n\n{sig_evaluator=}")

    # Generate test instance with desired signal evaluator
    test_inst = gen_testgentrades_inst(
        trading_config, risk_config, sig_eval_method=sig_evaluator
    )

    # Generate computed trades and signals
    computed_trades, computed_signals = test_inst.iterate_df("AAPL", sample_gen_trades)

    # Get expected_trades
    expected_trades = pd.read_parquet(f"./tests/data/{parquet_path}")

    print(f"computed_signals : \n\n{computed_signals}\n")
    print(f"sample_gen_trades : \n\n{sample_gen_trades}\n")
    print(f"\n\ncomputed_trades : \n\n{computed_trades}\n")
    print(f"expected_trades : \n\n{expected_trades}\n")

    pdt.assert_frame_equal(computed_trades, expected_trades)
    pdt.assert_frame_equal(computed_signals, sample_gen_trades)


def test_iterate_df_fixedexit(trading_config, risk_config, sample_gen_trades):
    """Test 'iterate_df' method in 'GenTrades' using 'FixedExit' strategy and
    'OpenEvaluator' signal evaluator."""

    risk = 5

    # Generate test DataFrame
    df = sample_gen_trades.copy()
    df = gen_test_df(df, risk)
    print(f"\n\n{df}\n")

    for col in df:
        print(f"{col:<15} : {set([type(record) for record in df[col]])}")

    # # Generate test instance with 'FixedExit' strategy
    # test_inst = gen_testgentrades_inst(
    #     trading_config, risk_config, exit_struct="FixedExit"
    # )

    # # Generate computed trades and signals
    # computed_trades, computed_signals = test_inst.iterate_df("AAPL", sample_gen_trades)

    # print(f"\n\ncomputed_trades : \n\n{pformat(computed_trades, sort_dicts=False)}\n")
    # print(f"computed_signals : \n\n{pformat(computed_signals, sort_dicts=False)}\n")
