"""Tests for TradingStrategy coordination and signal pipeline."""

import random
import re

import pandas as pd
import pytest

from strat_backtest.base.gen_trades import GenTrades
from strat_backtest.base.trade_signal import EntrySignal, ExitSignal
from strat_backtest.trade_strategy import TradingStrategy
from strat_backtest.utils.constants import EntryType


class SimpleTestEntrySignal(EntrySignal):
    """Test EntrySignal that restores entry_signal column from original sample_gen_trades."""

    def __init__(self, original_signals: pd.DataFrame, entry_type: EntryType = "long"):
        super().__init__(entry_type)
        self.original_signals = original_signals

    def gen_entry_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        # Merge back the entry_signal column based on date matching
        df_with_signals = df.merge(
            self.original_signals[["date", "entry_signal"]], on="date", how="left"
        )
        # Validate signals match entry_type constraints
        self._validate_entry_signal(df_with_signals)
        return df_with_signals


class SimpleTestExitSignal(ExitSignal):
    """Test ExitSignal that restores exit_signal column from original sample_gen_trades."""

    def __init__(self, original_signals: pd.DataFrame, entry_type: EntryType = "long"):
        super().__init__(entry_type)
        self.original_signals = original_signals

    def gen_exit_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        # Merge back the exit_signal column based on date matching
        df_with_signals = df.merge(
            self.original_signals[["date", "exit_signal"]], on="date", how="left"
        )
        # Validate signals match entry_type constraints
        self._validate_exit_signal(df_with_signals)
        return df_with_signals


class BrokenEntrySignal(EntrySignal):
    """Test EntrySignal that fails in various production-realistic ways with single-point corruption."""

    def __init__(self, failure_mode: str, entry_type: EntryType = "long"):
        super().__init__(entry_type)
        self.failure_mode = failure_mode

    def gen_entry_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        match self.failure_mode:
            case "missing_column":
                result_df = df.copy()
            case "invalid_signal_values":
                result_df = self._corrupt_with_invalid_signals(df)
            case "wrong_entry_type":
                result_df = self._corrupt_with_wrong_entry_type(df)
            case "corrupted_data":
                result_df = self._corrupt_with_none_values(df)
            case _:
                result_df = self._generate_working_signals(df)

        self._validate_entry_signal(result_df)
        return result_df

    def _corrupt_with_invalid_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert a single invalid signal at random index."""
        df_copy = df.copy()
        signals = ["wait"] * len(df)

        # Corrupt single random index
        corrupt_idx = random.choice(df.index.to_list())
        invalid_signals = ["invalid_signal", "corrupted", "null", ""]
        signals[corrupt_idx] = random.choice(invalid_signals)

        df_copy["entry_signal"] = signals
        return df_copy

    def _corrupt_with_wrong_entry_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert wrong signal type at random index."""
        df_copy = df.copy()
        signals = ["wait"] * len(df)

        corrupt_idx = random.choice(df.index.to_list())
        match self.entry_type:
            case "long":
                signals[corrupt_idx] = "sell"  # Invalid for long-only
            case "short":
                signals[corrupt_idx] = "buy"  # Invalid for short-only
            case _:  # longshort - no corruption needed
                pass

        df_copy["entry_signal"] = signals
        return df_copy

    def _corrupt_with_none_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert None at random index."""
        df_copy = df.copy()
        signals = ["wait"] * len(df)

        # Corrupt single random index with None
        corrupt_idx = random.choice(df.index.to_list())
        signals[corrupt_idx] = None

        df_copy["entry_signal"] = signals
        return df_copy

    def _generate_working_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate working signals for default case."""
        df_copy = df.copy()
        df_copy["entry_signal"] = "wait"
        return df_copy


class BrokenExitSignal(ExitSignal):
    """Test ExitSignal that fails in various production-realistic ways with single-point corruption."""

    def __init__(self, failure_mode: str, entry_type: EntryType = "long"):
        super().__init__(entry_type)
        self.failure_mode = failure_mode

    def gen_exit_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        match self.failure_mode:
            case "missing_column":
                result_df = df.copy()
            case "wrong_exit_type":
                result_df = self._corrupt_with_wrong_exit_type(df)
            case "runtime_error":
                raise RuntimeError("Database connection lost during signal calculation")
            case "mixed_corruption":
                result_df = self._corrupt_with_mixed_values(df)
            case _:
                result_df = self._generate_working_signals(df)

        self._validate_exit_signal(result_df)
        return result_df

    def _corrupt_with_wrong_exit_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert wrong exit signal type at random index."""
        df_copy = df.copy()
        signals = ["wait"] * len(df)

        corrupt_idx = random.choice(df.index.to_list())
        match self.entry_type:
            case "long":
                signals[corrupt_idx] = "buy"  # Invalid for long-only (should be sell)
            case "short":
                signals[corrupt_idx] = "sell"  # Invalid for short-only (should be buy)
            case _:  # longshort - no corruption needed
                pass

        df_copy["exit_signal"] = signals
        return df_copy

    def _corrupt_with_mixed_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert mixed corruption (None, invalid strings) at random index."""
        df_copy = df.copy()
        signals = ["wait"] * len(df)

        # Corrupt single random index with mixed corruption
        corrupt_idx = random.choice(df.index.to_list())
        corrupt_values = [None, "corrupted", "", "invalid_exit"]
        signals[corrupt_idx] = random.choice(corrupt_values)

        df_copy["exit_signal"] = signals
        return df_copy

    def _generate_working_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate working signals for default case."""
        df_copy = df.copy()
        df_copy["exit_signal"] = "wait"
        return df_copy


def test_trading_strategy_coordination(
    sample_ohlcv, sample_gen_trades, trading_config, risk_config
):
    """Test basic TradingStrategy coordination without mocking."""

    # Load expected results
    expected_df_trades = pd.read_parquet("tests/data/open_eval_trades.parquet")

    # Create signal instances locally
    simple_entry_signal = SimpleTestEntrySignal(sample_gen_trades, "long")
    simple_exit_signal = SimpleTestExitSignal(sample_gen_trades, "long")

    # Create GenTrades instance
    gen_trades = GenTrades(trading_config, risk_config)

    # Create TradingStrategy
    strategy = TradingStrategy(simple_entry_signal, simple_exit_signal, gen_trades)

    # Execute strategy
    df_trades, df_signals = strategy(sample_ohlcv)

    # Verify return types
    assert isinstance(df_trades, pd.DataFrame)
    assert isinstance(df_signals, pd.DataFrame)

    # Compare actual trades with expected trades
    pd.testing.assert_frame_equal(df_trades, expected_df_trades, check_dtype=True)

    # Verify signal columns exist
    assert "entry_signal" in df_signals.columns
    assert "exit_signal" in df_signals.columns


def test_signal_pipeline_flow(sample_ohlcv, sample_gen_trades):
    """Test step-by-step signal generation pipeline."""

    # Create signal instances locally
    simple_entry_signal = SimpleTestEntrySignal(sample_gen_trades, "long")
    simple_exit_signal = SimpleTestExitSignal(sample_gen_trades, "long")

    # Step 1: Add entry signals
    df_after_entry = simple_entry_signal.gen_entry_signal(sample_ohlcv)
    assert "entry_signal" in df_after_entry.columns
    pd.testing.assert_series_equal(
        df_after_entry["entry_signal"], sample_gen_trades["entry_signal"]
    )

    # Step 2: Add exit signals
    df_after_exit = simple_exit_signal.gen_exit_signal(df_after_entry)
    assert "exit_signal" in df_after_exit.columns
    pd.testing.assert_series_equal(
        df_after_exit["exit_signal"], sample_gen_trades["exit_signal"]
    )


def test_different_entry_types(
    sample_ohlcv, sample_gen_trades, trading_config, risk_config
):
    """Test TradingStrategy with different entry_type configurations."""

    # Test with longshort entry type (should accept both buy and sell)
    longshort_entry = SimpleTestEntrySignal(sample_gen_trades, "longshort")
    longshort_exit = SimpleTestExitSignal(sample_gen_trades, "longshort")

    gen_trades = GenTrades(trading_config, risk_config)
    strategy = TradingStrategy(longshort_entry, longshort_exit, gen_trades)

    df_trades, df_signals = strategy(sample_ohlcv)

    assert isinstance(df_trades, pd.DataFrame)
    assert isinstance(df_signals, pd.DataFrame)


def test_entry_signal_missing_column_error(sample_ohlcv, trading_config, risk_config):
    """Test ValueError when EntrySignal doesn't generate entry_signal column."""

    broken_entry = BrokenEntrySignal("missing_column", "long")
    simple_exit = BrokenExitSignal("working", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(broken_entry, simple_exit, gen_trades)

    with pytest.raises(ValueError, match="'entry_signal' column not found"):
        strategy(sample_ohlcv)


def test_exit_signal_missing_column_error(
    sample_ohlcv, sample_gen_trades, trading_config, risk_config
):
    """Test ValueError when ExitSignal doesn't generate exit_signal column."""

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    broken_exit = BrokenExitSignal("missing_column", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, broken_exit, gen_trades)

    with pytest.raises(ValueError, match="'exit_signal' column not found"):
        strategy(sample_ohlcv)


def test_invalid_entry_type_error():
    """Test ValueError for invalid EntryType during signal initialization."""

    with pytest.raises(ValueError, match="'invalid_type' is not a valid 'EntryType'"):
        BrokenEntrySignal("working", "invalid_type")  # type: ignore


def test_randomized_entry_signal_validation_error(
    sample_ohlcv, trading_config, risk_config
):
    """Test ValueError when some entry signals violate entry_type constraints."""

    # Long-only strategy that generates invalid sell signals
    broken_entry = BrokenEntrySignal("wrong_entry_type", "long")
    simple_exit = BrokenExitSignal("working", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(broken_entry, simple_exit, gen_trades)

    # Should hit validation error with corrupted signal
    with pytest.raises(
        ValueError, match="Long only strategy cannot generate sell entry signals"
    ):
        strategy(sample_ohlcv)


def test_randomized_exit_signal_validation_error(
    sample_ohlcv, sample_gen_trades, trading_config, risk_config
):
    """Test ValueError when some exit signals violate entry_type constraints."""

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    # Long-only strategy that generates invalid buy exit signals
    broken_exit = BrokenExitSignal("wrong_exit_type", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, broken_exit, gen_trades)

    # Should hit validation error with corrupted signal
    with pytest.raises(
        ValueError, match="Long only strategy cannot generate buy exit signals"
    ):
        strategy(sample_ohlcv)


def test_runtime_error_during_signal_generation(
    sample_ohlcv, sample_gen_trades, trading_config, risk_config
):
    """Test RuntimeError propagation during signal generation."""

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    broken_exit = BrokenExitSignal("runtime_error", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, broken_exit, gen_trades)

    with pytest.raises(
        RuntimeError, match="Database connection lost during signal calculation"
    ):
        strategy(sample_ohlcv)


def test_missing_ticker_column_error(sample_gen_trades, trading_config, risk_config):
    """Test ValueError when OHLCV DataFrame lacks required ticker column."""

    # Create DataFrame without ticker column
    df_no_ticker = sample_gen_trades.drop(
        columns=["ticker", "entry_signal", "exit_signal"]
    ).copy()

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    with pytest.raises(ValueError, match="DataFrame must contain a 'ticker' column"):
        strategy(df_no_ticker)


def test_multiple_tickers_error(
    sample_ohlcv, sample_gen_trades, trading_config, risk_config
):
    """Test ValueError when DataFrame contains multiple tickers."""

    # Create DataFrame with multiple tickers
    df_multi_ticker = sample_ohlcv.copy()
    df_multi_ticker.loc[5:, "ticker"] = "MSFT"  # Change half to different ticker

    unique_tickers = df_multi_ticker["ticker"].unique()
    expected_msg = f"DataFrame must contain exactly one ticker. Found: {unique_tickers}"

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    with pytest.raises(ValueError, match=re.escape(expected_msg)):
        strategy(df_multi_ticker)


def test_empty_dataframe_handling(sample_gen_trades, trading_config, risk_config):
    """Test handling of empty input DataFrame."""

    # Create empty DataFrame with required columns
    empty_df = pd.DataFrame(
        columns=["date", "ticker", "open", "high", "low", "close", "volume"]
    )

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    with pytest.raises(ValueError, match="Empty DataFrame is passed"):
        strategy(empty_df)


def test_malformed_ohlcv_data_error(sample_gen_trades, trading_config, risk_config):
    """Test error handling with malformed OHLCV data (missing required columns)."""

    # Create DataFrame missing required OHLCV columns
    incomplete_df = pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=5),
            "ticker": ["AAPL"] * 5,
            "open": [100, 101, 102, 103, 104],
            # Missing high, low, close, volume columns
        }
    )

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    # Should raise ValueError for missing required columns
    with pytest.raises(ValueError, match="required columns are missing"):
        strategy(incomplete_df)


def test_mixed_signal_corruption_handling(
    sample_ohlcv, sample_gen_trades, trading_config, risk_config
):
    """Test handling of mixed signal corruption (some None, some valid, some invalid strings)."""

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    # Exit signal with single-point mixed corruption
    broken_exit = BrokenExitSignal("mixed_corruption", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, broken_exit, gen_trades)

    # Should handle some level of corruption, but exact behavior depends on implementation
    # This test verifies the system doesn't crash with mixed corruption
    try:
        df_trades, df_signals = strategy(sample_ohlcv)
        # If successful, verify that signals DataFrame exists and has expected structure
        assert isinstance(df_signals, pd.DataFrame)
        assert "exit_signal" in df_signals.columns
    except (ValueError, TypeError) as e:
        # Corruption errors are acceptable - system should fail gracefully
        assert "signal" in str(e).lower() or "validation" in str(e).lower()
