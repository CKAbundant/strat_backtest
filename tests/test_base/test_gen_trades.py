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

from datetime import datetime

from ..test_utils import gen_takeall_completed_list


def test_init(gen_trades_inst):
    """Test '__init__' method for 'GenTrades' class."""

    assert gen_trades_inst.entry_struct == "MultiEntry"
    assert gen_trades_inst.exit_struct == "FIFOExit"
    assert gen_trades_inst.stop_method == "no_stop"
    assert gen_trades_inst.trail_method == "no_trail"


def test_exit_all(gen_trades_inst, open_trades):
    """Test 'exit_all' method for 'GenTrades' class."""

    # Set 'open_trades' attribute
    gen_trades_inst.open_trades = open_trades

    # Generate completed trade list based on 'exit_dt' datetime
    exit_dt = datetime(2025, 4, 14, tzinfo=None)
    exit_price = 202.52

    # Generate computed and expected completed list
    computed_list = gen_trades_inst.exit_all(exit_dt, exit_price)
    expected_list = gen_takeall_completed_list(open_trades, exit_dt, exit_price)

    assert set(computed_list) == set(expected_list)
