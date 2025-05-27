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

import pandas as pd
import pytest

from strat_backtest.base.gen_trades import GenTrades, RiskConfig, TradingConfig


class TestGenTrades(GenTrades):
    """Concrete implemenation for testing 'GenTrades' abstract class"""

    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(), pd.DataFrame()
