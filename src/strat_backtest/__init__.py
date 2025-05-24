"""High level direct import from 'strat_backtest' package:

- EntrySignal -> Abstract class for generating entry signal.
- ExitSignal -> abstract class for generating exit signal.
- GenTrades -> abstract class for generating completed trades during backtesting.
"""

from .base import EntrySignal, ExitSignal, GenTrades

# Public interface
__all__ = [
    "EntrySignal",
    "ExitSignal",
    "GenTrades",
]
