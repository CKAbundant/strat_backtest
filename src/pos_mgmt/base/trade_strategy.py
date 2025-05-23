"""Class to combine concrete implementation of 'EntrySignal', 'ExitSignal'
and 'GenTrades' into a strategy"""

import pandas as pd

from .gen_trades import GenTrades
from .trade_signal import EntrySignal, ExitSignal


class TradingStrategy:
    """Combine entry, profit and stop loss strategy as a complete trading strategy.

    Usage:
        >>> strategy = TradingStrategy(
                entry_type="long",
                entry=SentiEntry,
                exit=SentiExit,
                trades=SentiTrades,
            )
        >>> strategy.run()

    Args:
        entry_sig (EntrySignal):
            Class instance of concrete implementation of 'EntrySignal' abstract class.
        exit_sig (ExitSignal):
            Class instance of concrete implementation of 'ExitSignal'
            abstract class.
        trades (GetTrades):
            Class instance of concrete implementation of 'GetTrades' abstract class.

    Attributes:
        entry_sig (EntrySignal):
            Class instance of concrete implementation of 'EntrySignal' abstract class.
        exit_sig (ExitSignal):
            Class instance of concrete implementation of 'ExitSignal' abstract class.
        trades (GetTrades):
            Instance of concrete implementation of 'GetTrades' abstract class.
    """

    def __init__(
        self,
        entry_sig: EntrySignal,
        exit_sig: ExitSignal,
        trades: GenTrades,
    ) -> None:
        self.entry_sig = entry_sig
        self.exit_sig = exit_sig
        self.trades = trades

    def __call__(self, df_ohlcv: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Generate completed trades based on trading strategy i.e.
        combination of entry, profit exit and stop exit.

        Args:
            df_ohlcv (pd.DataFrame):
                DataFrame containing OHLCV data and TA (if any) for
                specific stock ticker.

        Returns:
            df_trades (pd.DataFrame):
                DataFrame containing completed trades.
            df_signals (pd.DataFrame):
                DataFrame containing updated exit signals price-related stops.
        """

        # Append entry and exit signal
        df_pa = self.entry_sig.gen_entry_signal(df_ohlcv)
        df_pa = self.exit_sig.gen_exit_signal(df_pa)

        # Generate trades
        df_trades, df_signals = self.trades.gen_trades(df_pa)

        return df_trades, df_signals
