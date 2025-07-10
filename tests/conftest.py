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


@pytest.fixture
def stop_info_list():
    """Generate sample 'stop_info_list' for testing 'append_info' method."""

    return [
        {
            "date": datetime(2025, 4, 10),
            "stop_price": 195.5,
            "stop_triggered": Decimal("1"),
        },
        {
            "date": datetime(2025, 4, 14),
            "stop_price": 199.2,
            "stop_triggered": Decimal("0"),
        },
    ]


@pytest.fixture
def long_records():
    """Generate sample 'records' list, which contains 'buy' entry signal and
    updated as an attribute to 'SignalEvaluator' class."""

    return [
        {
            "date": datetime(2025, 4, 4),
            "open": Decimal("193.64"),
            "high": Decimal("199.62"),
            "low": Decimal("187.09"),
            "close": Decimal("188.13"),
            "entry_signal": "buy",
            "exit_signal": "wait",
        },
        {
            "date": datetime(2025, 4, 7),
            "open": Decimal("176.97"),
            "high": Decimal("193.9"),
            "low": Decimal("174.39"),
            "close": Decimal("181.22"),
            "entry_signal": "wait",
            "exit_signal": "wait",
        },
        {
            "date": datetime(2025, 4, 8),
            "open": Decimal("186.46"),
            "high": Decimal("190.09"),
            "low": Decimal("168.99"),
            "close": Decimal("172.19"),
            "entry_signal": "buy",
            "exit_signal": "sell",
        },
    ]


@pytest.fixture
def short_records():
    """Generate sample 'records' list, which contains 'sell' entry signal and
    updated as an attribute to 'SignalEvaluator' class."""

    return [
        {
            "date": datetime(2025, 4, 10),
            "open": Decimal("188.82"),
            "high": Decimal("194.52"),
            "low": Decimal("182.76"),
            "close": Decimal("190.17"),
            "entry_signal": "sell",
            "exit_signal": "wait",
        },
        {
            "date": datetime(2025, 4, 11),
            "open": Decimal("185.86"),
            "high": Decimal("199.28"),
            "low": Decimal("185.82"),
            "close": Decimal("197.89"),
            "entry_signal": "sell",
            "exit_signal": "wait",
        },
        {
            "date": datetime(2025, 4, 14),
            "open": Decimal("211.16"),
            "high": Decimal("212.66"),
            "low": Decimal("200.90"),
            "close": Decimal("202.25"),
            "entry_signal": "wait",
            "exit_signal": "buy",
        },
    ]


@pytest.fixture
def error_records():
    """Generate sample 'records' list, which contains both 'buy' and 'sell'
    entry signal and  updated as an attribute to 'SignalEvaluator' class."""

    return [
        {
            "date": datetime(2025, 4, 10),
            "open": Decimal("188.82"),
            "high": Decimal("194.52"),
            "low": Decimal("182.76"),
            "close": Decimal("190.17"),
            "entry_signal": "buy",
            "exit_signal": "wait",
        },
        {
            "date": datetime(2025, 4, 11),
            "open": Decimal("185.86"),
            "high": Decimal("199.28"),
            "low": Decimal("185.82"),
            "close": Decimal("197.89"),
            "entry_signal": "wait",
            "exit_signal": "wait",
        },
        {
            "date": datetime(2025, 4, 14),
            "open": Decimal("211.16"),
            "high": Decimal("212.66"),
            "low": Decimal("200.90"),
            "close": Decimal("202.25"),
            "entry_signal": "sell",
            "exit_signal": "wait",
        },
    ]


@pytest.fixture
def long_success():
    """Next day record for 'long_records' and high above previous high."""

    return {
        "date": datetime(2025, 4, 9),
        "open": Decimal("171.72"),
        "high": Decimal("200.35"),
        "low": Decimal("171.66"),
        "close": Decimal("198.59"),
        "entry_signal": "buy",
        "exit_signal": "wait",
    }


@pytest.fixture
def long_fail():
    """Next day record for 'long_records' and high below previous high."""

    return {
        "date": datetime(2025, 4, 9),
        "open": Decimal("171.72"),
        "high": Decimal("190.09"),
        "low": Decimal("171.66"),
        "close": Decimal("189.59"),
        "entry_signal": "buy",
        "exit_signal": "wait",
    }


@pytest.fixture
def short_success():
    """Next day record for 'short_records'."""

    return {
        "date": datetime(2025, 4, 15),
        "open": Decimal("201.6"),
        "high": Decimal("203.24"),
        "low": Decimal("199.54"),
        "close": Decimal("201.88"),
        "entry_signal": "sell",
        "exit_signal": "wait",
    }


@pytest.fixture
def short_fail():
    """Next day record for 'short_records'."""

    return {
        "date": datetime(2025, 4, 15),
        "open": Decimal("201.6"),
        "high": Decimal("203.24"),
        "low": Decimal("200.9"),
        "close": Decimal("201.88"),
        "entry_signal": "sell",
        "exit_signal": "wait",
    }


@pytest.fixture
def no_entry():
    """Next day record for with no entry signal."""

    return {
        "date": datetime(2025, 4, 9),
        "open": Decimal("171.72"),
        "high": Decimal("200.35"),
        "low": Decimal("171.66"),
        "close": Decimal("198.59"),
        "entry_signal": "wait",
        "exit_signal": "wait",
    }
