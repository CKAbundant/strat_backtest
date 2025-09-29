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


# TODO: Implement RSI-based EntrySignal class
class RSIEntrySignal(EntrySignal):
    """Generate entry signals based on RSI indicators."""

    def gen_entry_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI-based entry signals.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added 'entry_signal' column
        """
        # TODO: Implement RSI entry logic
        pass


# TODO: Implement RSI-based ExitSignal class
class RSIExitSignal(ExitSignal):
    """Generate exit signals based on RSI indicators."""

    def gen_exit_signal(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate RSI-based exit signals.

        Args:
            df: DataFrame with OHLCV data and entry signals

        Returns:
            DataFrame with added 'exit_signal' column
        """
        # TODO: Implement RSI exit logic
        pass


def main():
    """Run the RSI trading strategy example."""

    # TODO: Load sample data
    # df_ohlcv = pd.read_parquet('examples/data/sample_ohlcv.parquet')

    # TODO: Configure trading parameters
    # trading_cfg = TradingConfig(
    #     entry_struct="SingleEntry",
    #     exit_struct="FIFOExit",
    #     num_lots=100,
    #     monitor_close=True
    # )

    # TODO: Configure risk management
    # risk_cfg = RiskConfig(
    #     sig_eval_method="OpenEvaluator",
    #     percent_loss=0.05,
    #     stop_method="PercentLoss"
    # )

    # TODO: Initialize strategy components
    # entry_signal = RSIEntrySignal("long")
    # exit_signal = RSIExitSignal("long")
    # trades = GenTrades(trading_cfg, risk_cfg)

    # TODO: Create complete strategy
    # strategy = TradingStrategy(
    #     entry_signal=entry_signal,
    #     exit_sig=exit_signal,
    #     trades=trades
    # )

    # TODO: Execute backtest
    # df_trades, df_signals = strategy(df_ohlcv)

    # TODO: Display results
    # print("Completed Trades:")
    # print(df_trades)

    print("RSI Strategy Example - Implementation Placeholder")
    print("TODO: Complete the RSI signal implementations above")


if __name__ == "__main__":
    main()
