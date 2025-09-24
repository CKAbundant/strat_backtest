# TradingStrategy Testing Implementation Plan

## Analysis Summary

### Sample Data Structure
The `sample_gen_trades.parquet` contains:
- **OHLCV columns**: date, ticker, open, high, low, close, volume
- **Signal columns**: entry_signal, exit_signal (with buy/wait/sell values)
- **10 rows** of AAPL data with realistic signal patterns
- **Signal distribution**:
  - Entry signals: 4 buy, 6 wait
  - Exit signals: 3 sell, 7 wait

### Testing Strategy
- **No mocking**: Use real GenTrades coordination logic
- **Signal restoration**: Merge back original signals from sample_gen_trades
- **Local instances**: Create signal classes in each test for isolation
- **Proper validation**: Call inherited validation methods
- **Clean separation**: Extract OHLCV fixture separate from signals

## Implementation Code

### 1. Clean OHLCV Fixture (add to conftest.py)
```python
@pytest.fixture
def sample_ohlcv(sample_gen_trades):
    """Extract clean OHLCV data from sample_gen_trades, removing signal columns."""
    return sample_gen_trades.drop(columns=['entry_signal', 'exit_signal'])
```

### 2. Complete Test File (tests/test_trade_strategy.py)
```python
"""Tests for TradingStrategy coordination and signal pipeline."""

import pandas as pd
import pytest
import random

from strat_backtest.base.trade_signal import EntrySignal, ExitSignal
from strat_backtest.base.gen_trades import GenTrades
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
            self.original_signals[['date', 'entry_signal']],
            on='date',
            how='left'
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
            self.original_signals[['date', 'exit_signal']],
            on='date',
            how='left'
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
                return df.copy()
            case "invalid_signal_values":
                return self._corrupt_with_invalid_signals(df)
            case "wrong_entry_type":
                return self._corrupt_with_wrong_entry_type(df)
            case "corrupted_data":
                return self._corrupt_with_none_values(df)
            case _:
                return self._generate_working_signals(df)

    def _corrupt_with_invalid_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert a single invalid signal at random index."""
        df_copy = df.copy()
        signals = ['wait'] * len(df)

        # Corrupt single random index
        corrupt_idx = random.choice(df.index.to_list())
        invalid_signals = ['invalid_signal', 'corrupted', 'null', '']
        signals[corrupt_idx] = random.choice(invalid_signals)

        df_copy['entry_signal'] = signals
        return df_copy

    def _corrupt_with_wrong_entry_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert wrong signal type at random index."""
        df_copy = df.copy()
        signals = ['wait'] * len(df)

        corrupt_idx = random.choice(df.index.to_list())
        match self.entry_type:
            case "long":
                signals[corrupt_idx] = 'sell'  # Invalid for long-only
            case "short":
                signals[corrupt_idx] = 'buy'   # Invalid for short-only
            case _:  # longshort - no corruption needed
                pass

        df_copy['entry_signal'] = signals
        return df_copy

    def _corrupt_with_none_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert None at random index."""
        df_copy = df.copy()
        signals = ['wait'] * len(df)

        # Corrupt single random index with None
        corrupt_idx = random.choice(df.index.to_list())
        signals[corrupt_idx] = None

        df_copy['entry_signal'] = signals
        return df_copy

    def _generate_working_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate working signals for default case."""
        df_copy = df.copy()
        df_copy['entry_signal'] = 'wait'
        return df_copy


class BrokenExitSignal(ExitSignal):
    """Test ExitSignal that fails in various production-realistic ways with single-point corruption."""

    def __init__(self, failure_mode: str, entry_type: EntryType = "long"):
        super().__init__(entry_type)
        self.failure_mode = failure_mode

    def gen_exit_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        match self.failure_mode:
            case "missing_column":
                return df.copy()
            case "wrong_exit_type":
                return self._corrupt_with_wrong_exit_type(df)
            case "runtime_error":
                raise RuntimeError("Database connection lost during signal calculation")
            case "mixed_corruption":
                return self._corrupt_with_mixed_values(df)
            case _:
                return self._generate_working_signals(df)

    def _corrupt_with_wrong_exit_type(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert wrong exit signal type at random index."""
        df_copy = df.copy()
        signals = ['wait'] * len(df)

        corrupt_idx = random.choice(df.index.to_list())
        match self.entry_type:
            case "long":
                signals[corrupt_idx] = 'buy'   # Invalid for long-only (should be sell)
            case "short":
                signals[corrupt_idx] = 'sell'  # Invalid for short-only (should be buy)
            case _:  # longshort - no corruption needed
                pass

        df_copy['exit_signal'] = signals
        return df_copy

    def _corrupt_with_mixed_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Insert mixed corruption (None, invalid strings) at random index."""
        df_copy = df.copy()
        signals = ['wait'] * len(df)

        # Corrupt single random index with mixed corruption
        corrupt_idx = random.choice(df.index.to_list())
        corrupt_values = [None, 'corrupted', '', 'invalid_exit']
        signals[corrupt_idx] = random.choice(corrupt_values)

        df_copy['exit_signal'] = signals
        return df_copy

    def _generate_working_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate working signals for default case."""
        df_copy = df.copy()
        df_copy['exit_signal'] = 'wait'
        return df_copy


def test_trading_strategy_coordination(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
    """Test basic TradingStrategy coordination without mocking."""

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

    # Verify signal columns exist
    assert 'entry_signal' in df_signals.columns
    assert 'exit_signal' in df_signals.columns


def test_signal_pipeline_flow(sample_ohlcv, sample_gen_trades):
    """Test step-by-step signal generation pipeline."""

    # Create signal instances locally
    simple_entry_signal = SimpleTestEntrySignal(sample_gen_trades, "long")
    simple_exit_signal = SimpleTestExitSignal(sample_gen_trades, "long")

    # Step 1: Add entry signals
    df_after_entry = simple_entry_signal.gen_entry_signal(sample_ohlcv)
    assert 'entry_signal' in df_after_entry.columns
    assert df_after_entry['entry_signal'].equals(sample_gen_trades['entry_signal'])

    # Step 2: Add exit signals
    df_after_exit = simple_exit_signal.gen_exit_signal(df_after_entry)
    assert 'exit_signal' in df_after_exit.columns
    assert df_after_exit['exit_signal'].equals(sample_gen_trades['exit_signal'])


def test_different_entry_types(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
    """Test TradingStrategy with different entry_type configurations."""

    # Test with longshort entry type (should accept both buy and sell)
    longshort_entry = SimpleTestEntrySignal(sample_gen_trades, "longshort")
    longshort_exit = SimpleTestExitSignal(sample_gen_trades, "longshort")

    gen_trades = GenTrades(trading_config, risk_config)
    strategy = TradingStrategy(longshort_entry, longshort_exit, gen_trades)

    df_trades, df_signals = strategy(sample_ohlcv)

    assert isinstance(df_trades, pd.DataFrame)
    assert isinstance(df_signals, pd.DataFrame)


def test_strategy_return_format(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
    """Test that TradingStrategy returns properly formatted DataFrames."""

    simple_entry_signal = SimpleTestEntrySignal(sample_gen_trades, "long")
    simple_exit_signal = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(simple_entry_signal, simple_exit_signal, gen_trades)
    df_trades, df_signals = strategy(sample_ohlcv)

    # Verify df_trades has expected trade columns (based on StockTrade model)
    expected_trade_cols = ['ticker', 'entry_datetime', 'entry_action', 'entry_lots',
                          'entry_price', 'exit_datetime', 'exit_action', 'exit_lots',
                          'exit_price']

    # Check that some expected columns exist (df_trades might be empty if no trades completed)
    if not df_trades.empty:
        for col in ['ticker', 'entry_datetime', 'entry_action']:
            assert col in df_trades.columns

    # Verify df_signals has original OHLCV + signal columns
    expected_signal_cols = ['date', 'ticker', 'open', 'high', 'low', 'close',
                           'volume', 'entry_signal', 'exit_signal']
    for col in expected_signal_cols:
        assert col in df_signals.columns


def test_entry_signal_missing_column_error(sample_ohlcv, trading_config, risk_config):
    """Test ValueError when EntrySignal doesn't generate entry_signal column."""

    broken_entry = BrokenEntrySignal("missing_column", "long")
    simple_exit = BrokenExitSignal("working", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(broken_entry, simple_exit, gen_trades)

    with pytest.raises(ValueError, match="'entry_signal' column not found!"):
        strategy(sample_ohlcv)


def test_exit_signal_missing_column_error(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
    """Test ValueError when ExitSignal doesn't generate exit_signal column."""

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    broken_exit = BrokenExitSignal("missing_column", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, broken_exit, gen_trades)

    with pytest.raises(ValueError, match="'exit_signal' column not found!"):
        strategy(sample_ohlcv)


def test_invalid_entry_type_error():
    """Test ValueError for invalid EntryType during signal initialization."""

    with pytest.raises(ValueError, match="'invalid_type' is not a valid 'EntryType'"):
        BrokenEntrySignal("working", "invalid_type")  # type: ignore


def test_randomized_entry_signal_validation_error(sample_ohlcv, trading_config, risk_config):
    """Test ValueError when some entry signals violate entry_type constraints."""

    # Long-only strategy that generates invalid sell signals
    broken_entry = BrokenEntrySignal("wrong_entry_type", "long")
    simple_exit = BrokenExitSignal("working", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(broken_entry, simple_exit, gen_trades)

    # Should hit validation error with corrupted signal
    with pytest.raises(ValueError, match="Long only strategy cannot generate sell entry signals"):
        strategy(sample_ohlcv)


def test_randomized_exit_signal_validation_error(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
    """Test ValueError when some exit signals violate entry_type constraints."""

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    # Long-only strategy that generates invalid buy exit signals
    broken_exit = BrokenExitSignal("wrong_exit_type", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, broken_exit, gen_trades)

    # Should hit validation error with corrupted signal
    with pytest.raises(ValueError, match="Long only strategy cannot generate buy exit signals"):
        strategy(sample_ohlcv)


def test_runtime_error_during_signal_generation(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
    """Test RuntimeError propagation during signal generation."""

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    broken_exit = BrokenExitSignal("runtime_error", "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, broken_exit, gen_trades)

    with pytest.raises(RuntimeError, match="Database connection lost during signal calculation"):
        strategy(sample_ohlcv)


def test_missing_ticker_column_error(sample_gen_trades, trading_config, risk_config):
    """Test ValueError when OHLCV DataFrame lacks required ticker column."""

    # Create DataFrame without ticker column
    df_no_ticker = sample_gen_trades.drop(columns=['ticker', 'entry_signal', 'exit_signal']).copy()

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    with pytest.raises(ValueError, match="DataFrame must contain a 'ticker' column"):
        strategy(df_no_ticker)


def test_multiple_tickers_error(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
    """Test ValueError when DataFrame contains multiple tickers."""

    # Create DataFrame with multiple tickers
    df_multi_ticker = sample_ohlcv.copy()
    df_multi_ticker.loc[5:, 'ticker'] = 'MSFT'  # Change half to different ticker

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    with pytest.raises(ValueError, match="DataFrame contains multiple tickers"):
        strategy(df_multi_ticker)


def test_empty_dataframe_handling(sample_gen_trades, trading_config, risk_config):
    """Test handling of empty input DataFrame."""

    # Create empty DataFrame with required columns
    empty_df = pd.DataFrame(columns=['date', 'ticker', 'open', 'high', 'low', 'close', 'volume'])

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    # Should handle empty DataFrame gracefully - may raise error or return empty results
    try:
        df_trades, df_signals = strategy(empty_df)
        # If it doesn't raise an error, verify empty results
        assert df_trades.empty or len(df_trades) == 0
        assert df_signals.empty or len(df_signals) == 0
    except ValueError:
        # Empty DataFrame error is also acceptable behavior
        pass


def test_malformed_ohlcv_data_error(sample_gen_trades, trading_config, risk_config):
    """Test error handling with malformed OHLCV data (missing required columns)."""

    # Create DataFrame missing required OHLCV columns
    incomplete_df = pd.DataFrame({
        'date': pd.date_range('2023-01-01', periods=5),
        'ticker': ['AAPL'] * 5,
        'open': [100, 101, 102, 103, 104],
        # Missing high, low, close, volume columns
    })

    working_entry = SimpleTestEntrySignal(sample_gen_trades, "long")
    working_exit = SimpleTestExitSignal(sample_gen_trades, "long")
    gen_trades = GenTrades(trading_config, risk_config)

    strategy = TradingStrategy(working_entry, working_exit, gen_trades)

    # Should raise ValueError for missing required columns
    with pytest.raises(ValueError, match="required columns are missing"):
        strategy(incomplete_df)


def test_mixed_signal_corruption_handling(sample_ohlcv, sample_gen_trades, trading_config, risk_config):
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
        assert 'exit_signal' in df_signals.columns
    except (ValueError, TypeError) as e:
        # Corruption errors are acceptable - system should fail gracefully
        assert "signal" in str(e).lower() or "validation" in str(e).lower()
```

## Key Benefits

### Technical Advantages
- **Self-contained**: All test classes and functions in single test file
- **Local instance creation**: Each test creates its own signal instances for isolation
- **Flexible testing**: Can easily test different entry_type combinations per test
- **Proper validation**: Calls inherited `_validate_entry_signal()` and `_validate_exit_signal()` methods

### Testing Quality
- **No mocking**: Uses real GenTrades coordination logic for authentic integration testing
- **Predictable signals**: Restores original signals from sample_gen_trades for consistent results
- **Clean separation**: OHLCV fixture separate from signal logic
- **Realistic testing**: Uses actual sample_gen_trades data patterns with real market data

### Coverage Areas
1. **Basic coordination**: TradingStrategy orchestrates EntrySignal → ExitSignal → GenTrades
2. **Pipeline flow**: Step-by-step signal generation and DataFrame transformation
3. **Signal validation**: Inherited validation methods catch invalid combinations
4. **Entry type flexibility**: Support for long, short, and longshort strategies
5. **Return format validation**: Proper DataFrame structure and column presence
6. **Error conditions**: Production-realistic failure modes with randomized errors
7. **Data corruption**: Mixed corruption scenarios (None, invalid strings, missing columns)
8. **Runtime errors**: Exception propagation and graceful failure handling
9. **Input validation**: Malformed OHLCV data and missing required columns
10. **Edge cases**: Empty DataFrames and multiple ticker validation

## Usage Instructions

1. **Add fixture**: Add `sample_ohlcv` fixture to `tests/conftest.py`
2. **Create test file**: Create `tests/test_trade_strategy.py` with complete implementation
3. **Run tests**: Execute with `uv run pytest tests/test_trade_strategy.py -v`
4. **Extend coverage**: Add more test cases for edge cases and error conditions

This implementation provides comprehensive TradingStrategy testing without mocking, ensuring the coordination logic works correctly with real component implementations.