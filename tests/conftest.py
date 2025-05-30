"""All fixtures automatically available for testing"""

from collections import deque
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd
import pytest

from strat_backtest.base.gen_trades import RiskConfig, TradingConfig
from strat_backtest.base.stock_trade import StockTrade

FIXTURE_DIR = Path(__file__).parent


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
        trigger_trail=0.05,
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
def open_trades():
    """Generate sample deque list of 'StockTrade' pydantic object"""

    first_trade = StockTrade(
        ticker="AAPL",
        entry_datetime=datetime(2025, 4, 7, tzinfo=None),
        entry_action="buy",
        entry_lots=10,
        entry_price=181.46,
    )

    second_trade = StockTrade(
        ticker="AAPL",
        entry_datetime=datetime(2025, 4, 8, tzinfo=None),
        entry_action="buy",
        entry_lots=10,
        entry_price=172.42,
    )

    third_trade = StockTrade(
        ticker="AAPL",
        entry_datetime=datetime(2025, 4, 11, tzinfo=None),
        entry_action="buy",
        entry_lots=10,
        entry_price=198.15,
    )

    return deque([first_trade, second_trade, third_trade])


@pytest.fixture
def completed_list():
    """Generate sample 'completed_list' i.e. list of dictionary containing
    completed stock trade info."""

    return [
        {
            "ticker": "AAPL",
            "entry_datetime": datetime(2025, 3, 25, 0, 0),
            "entry_action": "buy",
            "entry_lots": Decimal("10"),
            "entry_price": Decimal("223.75"),
            "exit_datetime": datetime(2025, 3, 28, 0, 0),
            "exit_action": "sell",
            "exit_lots": Decimal("10"),
            "exit_price": Decimal("217.9"),
            "days_held": 3,
            "profit_loss": Decimal("-5.85"),
            "percent_ret": Decimal("-0.026145"),
            "daily_ret": Decimal("-0.008792"),
            "win": 0,
        }
    ]
