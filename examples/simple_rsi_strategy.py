"""Simple RSI trading strategy example using strat_backtest framework.

This example demonstrates how to implement a basic RSI momentum strategy
using the modular components of the strat_backtest framework.
"""

import numpy as np
import pandas as pd
import talib

from strat_backtest import (
    EntrySignal,
    ExitSignal,
    GenTrades,
    RiskConfig,
    TradingConfig,
    TradingStrategy,
)


class RSIEntrySignal(EntrySignal):
    """Generate entry signals based on RSI indicators."""

    def gen_entry_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI-based entry signals.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added 'entry_signal' column
        """
        # Calculate RSI(14) using TA-Lib
        df_copy = df.copy()
        close_prices = df_copy["close"].astype(float).values
        df_copy["RSI_14"] = talib.RSI(close_prices, timeperiod=14)

        # Generate entry signals: buy when RSI < 30, otherwise wait
        df_copy["entry_signal"] = np.where(df_copy["RSI_14"] < 30, "buy", "wait")

        # Validate entry signals before returning
        self._validate_entry_signal(df_copy)

        return df_copy


class RSIExitSignal(ExitSignal):
    """Generate exit signals based on RSI indicators."""

    def gen_exit_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI-based exit signals.

        Args:
            df: DataFrame with OHLCV data and entry signals

        Returns:
            DataFrame with added 'exit_signal' column
        """
        # Read RSI values from existing RSI_14 column
        df_copy = df.copy()

        # Generate exit signals: sell when RSI > 70, otherwise wait
        df_copy["exit_signal"] = np.where(df_copy["RSI_14"] > 70, "sell", "wait")

        # Validate exit signals before returning
        self._validate_exit_signal(df_copy)

        return df_copy


def main():
    """Run the RSI trading strategy example."""

    # Load sample data
    df_ohlcv = pd.read_parquet("examples/data/sample_ohlcv.parquet")

    # Config trading parameters. monitor_close defaults to True.
    trading_cfg = TradingConfig(
        entry_struct="SingleEntry",
        exit_struct="FIFOExit",
        num_lots=100,
    )

    # Configure risk management using all default values:
    # sig_eval_method="OpenEvaluator", trigger_percent=None, percent_loss=0.05,
    # stop_method="no_stop", trail_method="no_trail", trigger_trail=0.2, step=None
    risk_cfg = RiskConfig()

    # Initialize strategy components
    entry_signal = RSIEntrySignal("long")
    exit_signal = RSIExitSignal("long")
    trades = GenTrades(trading_cfg, risk_cfg)

    # Create complete strategy
    strategy = TradingStrategy(
        entry_signal=entry_signal, exit_sig=exit_signal, trades=trades
    )

    # Execute backtest
    df_trades, df_signals = strategy(df_ohlcv)

    # Display results
    print("Completed Trades:")
    print(df_trades)
    print("\nSignals Summary:")
    print(df_signals[["RSI_14", "entry_signal", "exit_signal"]].tail())


if __name__ == "__main__":
    main()
