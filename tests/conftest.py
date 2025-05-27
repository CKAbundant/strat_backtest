"""All fixtures automatically available for testing"""

from collections import deque
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from strat_backtest.base.gen_trades import GenTrades, RiskConfig, TradingConfig
from strat_backtest.base.stock_trade import StockTrade

FIXTURE_DIR = Path(__file__).parent


class TestGenTrades(GenTrades):
    """Concrete implemenation for testing 'GenTrades' abstract class"""

    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(), pd.DataFrame()


@pytest.fixture
def trading_config():
    return TradingConfig(
        entry_struct="MultiEntry",
        exit_struct="FIFOExit",
        num_lots=10,
        monitor_close=True,
    )


@pytest.fixture
def risk_config():
    return RiskConfig(
        percent_loss=0.05,
        stop_method="no_stop",
        trail_method="no_trail",
        step=None,
    )


@pytest.fixture
def sample_gen_trades():
    """Load 'sample_gen_trades.parquet' as fixture."""

    parquet_path = FIXTURE_DIR.joinpath("data", "sample_gen_trades.parquet")

    if not parquet_path.is_file():
        raise FileNotFoundError(
            f"sample_gen_trades.parquet doesn't exist at '{parquet_path.as_posix()}'"
        )

    return pd.read_parquet(parquet_path)


@pytest.fixture
def gen_trades_inst(trading_config, risk_config):
    """Generate instance of 'TestGenTrades' to test non-abstract methods."""

    return TestGenTrades(trading_config, risk_config)


@pytest.fixture
def open_trades():
    """Generate sample deque list of 'StockTrade' pydantic object"""

    first_trade = StockTrade(
        ticker="AAPL",
        entry_datetime=datetime(2025, 4, 2, tzinfo=None),
        entry_action="buy",
        entry_lots=10,
        entry_price=223.89,
    )

    second_trade = StockTrade(
        ticker="AAPL",
        entry_datetime=datetime(2025, 4, 3, tzinfo=None),
        entry_action="buy",
        entry_lots=10,
        entry_price=203.19,
    )

    third_trade = StockTrade(
        ticker="AAPL",
        entry_datetime=datetime(2025, 4, 8, tzinfo=None),
        entry_action="buy",
        entry_lots=10,
        entry_price=172.42,
    )

    return deque([first_trade, second_trade, third_trade])
