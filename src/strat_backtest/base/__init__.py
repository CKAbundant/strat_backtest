"""Import abstract classes to be accessible at 'base' sub-package."""

# Abstract classes to generate strategy and perform backtesting
# Configuration dataclasses
from .data_class import RiskConfig, TradingConfig
from .entry_struct import EntryStruct
from .exit_struct import ExitStruct, HalfExitStruct
from .gen_trades import GenTrades
from .signal_evaluator import SignalEvaluator

# Pydantic object to record completed trade
from .stop_loss import StopLoss
from .trade_signal import EntrySignal, ExitSignal
from .trail_profit import TrailProfit

# Public interface
__all__ = [
    "EntryStruct",
    "ExitStruct",
    "HalfExitStruct",
    "GenTrades",
    "StopLoss",
    "TrailProfit",
    "EntrySignal",
    "ExitSignal",
    "SignalEvaluator",
    "RiskConfig",
    "TradingConfig",
]
