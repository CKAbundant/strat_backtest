"""Test ticker validation functionality in GenTrades.gen_trades method.

Tests the new validation logic implemented when converting GenTrades
from abstract to concrete class.
"""

import pandas as pd
import pytest

from strat_backtest.base.gen_trades import GenTrades


class TestGenTradesTickerValidation:
    """Test ticker validation in GenTrades.gen_trades method."""

    def test_missing_ticker_column_raises_error(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Test that missing ticker column raises ValueError."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Modify sample data to remove ticker column
        df_no_ticker = sample_gen_trades.drop(columns=["ticker"])

        # Act & Assert
        with pytest.raises(
            ValueError, match="DataFrame must contain a 'ticker' column"
        ):
            gen_trades.gen_trades(df_no_ticker)

    def test_multiple_tickers_raises_error(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Test that multiple tickers in DataFrame raises ValueError."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Modify sample data to have multiple tickers
        df_multi_ticker = sample_gen_trades.copy()
        # Change first few rows to different ticker
        df_multi_ticker.loc[0:2, "ticker"] = "MSFT"

        # Act & Assert
        expected_message = (
            "DataFrame must contain exactly one ticker. Found: \\['MSFT' 'AAPL'\\]"
        )
        with pytest.raises(ValueError, match=expected_message):
            gen_trades.gen_trades(df_multi_ticker)

    def test_single_ticker_success_delegates_to_iterate_df(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Test that single ticker DataFrame successfully delegates to iterate_df."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Use the sample data as-is (already has single ticker 'AAPL')
        assert "ticker" in sample_gen_trades.columns
        assert len(sample_gen_trades["ticker"].unique()) == 1
        assert sample_gen_trades["ticker"].iloc[0] == "AAPL"

        # Act - This should work without errors and call iterate_df internally
        df_trades, df_signals = gen_trades.gen_trades(sample_gen_trades)

        # Assert - Verify the method executed and returned expected types
        assert isinstance(df_trades, pd.DataFrame)
        assert isinstance(df_signals, pd.DataFrame)
        # Verify we get back the same number of rows in df_signals
        assert len(df_signals) == len(sample_gen_trades)

    def test_single_ticker_extracts_correct_ticker_string(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Test that ticker is correctly extracted as string and passed to iterate_df."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Modify sample data to use different ticker
        df_single_ticker = sample_gen_trades.copy()
        df_single_ticker["ticker"] = "TSLA"  # Change all ticker values to TSLA

        # Act - Should extract 'TSLA' as ticker and pass to iterate_df
        df_trades, df_signals = gen_trades.gen_trades(df_single_ticker)

        # Assert - Method completed successfully
        assert isinstance(df_trades, pd.DataFrame)
        assert isinstance(df_signals, pd.DataFrame)

    def test_ticker_validation_with_numeric_ticker(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Test that numeric tickers are converted to string correctly."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Modify sample data to have numeric ticker
        df_numeric_ticker = sample_gen_trades.copy()
        df_numeric_ticker["ticker"] = 123  # Set all ticker values to numeric

        # Act - Should convert numeric ticker to string
        df_trades, df_signals = gen_trades.gen_trades(df_numeric_ticker)

        # Assert - Method completed successfully
        assert isinstance(df_trades, pd.DataFrame)
        assert isinstance(df_signals, pd.DataFrame)

    def test_empty_dataframe_with_ticker_column(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Test that empty DataFrame with ticker column raises appropriate error."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Create empty DataFrame with same structure as sample_gen_trades
        df_empty = sample_gen_trades.iloc[0:0].copy()  # Keep structure but no rows

        # Act & Assert - Should raise error for no tickers found
        with pytest.raises(
            ValueError, match="DataFrame must contain exactly one ticker. Found: \\[\\]"
        ):
            gen_trades.gen_trades(df_empty)

    def test_real_data_integration_with_sample_fixture(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Integration test using real sample data to ensure full workflow works."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Load expected trades from parquet file
        expected_trades = pd.read_parquet("tests/data/open_eval_trades.parquet")

        # Verify sample data has proper structure
        required_cols = [
            "date",
            "ticker",
            "open",
            "high",
            "low",
            "close",
            "entry_signal",
            "exit_signal",
        ]
        for col in required_cols:
            assert col in sample_gen_trades.columns, f"Missing required column: {col}"

        # Act - Full integration test with real data
        df_trades, df_signals = gen_trades.gen_trades(sample_gen_trades)

        # Assert - Verify output structure and content
        assert isinstance(df_trades, pd.DataFrame)
        assert isinstance(df_signals, pd.DataFrame)

        # Verify df_signals preserves original data structure
        assert len(df_signals) == len(sample_gen_trades)
        assert all(col in df_signals.columns for col in sample_gen_trades.columns)

        # Compare actual trades with expected trades
        assert (
            not df_trades.empty
        ), "Expected trades to be generated but got empty DataFrame"

        # Verify same shape
        assert (
            df_trades.shape == expected_trades.shape
        ), f"Shape mismatch: actual {df_trades.shape} vs expected {expected_trades.shape}"

        # Verify same columns
        assert list(df_trades.columns) == list(
            expected_trades.columns
        ), f"Column mismatch: actual {list(df_trades.columns)} vs expected {list(expected_trades.columns)}"

        # Compare DataFrames using pandas testing (order should match exactly)
        pd.testing.assert_frame_equal(
            df_trades,
            expected_trades,
            check_dtype=False,  # Allow for slight type differences (e.g., object vs Decimal)
            rtol=1e-5,  # Relative tolerance for floating point comparisons
            atol=1e-8,  # Absolute tolerance for floating point comparisons
        )

    def test_three_different_tickers_error_message(
        self, trading_config, risk_config, sample_gen_trades
    ):
        """Test error message with three different tickers to verify unique ticker extraction."""
        # Arrange
        gen_trades = GenTrades(trading_config, risk_config)

        # Modify sample data to have three different tickers
        df_multi_ticker = sample_gen_trades.copy()
        num_rows = len(df_multi_ticker)
        third = num_rows // 3

        df_multi_ticker.loc[0 : third - 1, "ticker"] = "MSFT"
        df_multi_ticker.loc[third : 2 * third - 1, "ticker"] = "TSLA"
        df_multi_ticker.loc[2 * third :, "ticker"] = "AAPL"

        # Act & Assert - Should list all three unique tickers
        expected_message = "DataFrame must contain exactly one ticker. Found: \\['MSFT' 'TSLA' 'AAPL'\\]"
        with pytest.raises(ValueError, match=expected_message):
            gen_trades.gen_trades(df_multi_ticker)
