"""High level direct import from 'strat_backtest' package:

- EntrySignal -> Abstract class for generating entry signal.
- ExitSignal -> abstract class for generating exit signal.
- GenTrades -> abstract class for generating completed trades during backtesting.
- TradingStrategy -> Main coordinator that processes signals into completed trades.
- TradingConfig -> Configuration for trading parameters.
- RiskConfig -> Configuration for risk management parameters.
"""

from .base import EntrySignal, ExitSignal, GenTrades, RiskConfig, TradingConfig
from .trade_strategy import TradingStrategy

# Public interface
__all__ = [
    "EntrySignal",
    "ExitSignal",
    "GenTrades",
    "TradingStrategy",
    "TradingConfig",
    "RiskConfig",
]
