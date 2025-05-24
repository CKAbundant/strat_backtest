"""Import abstract classes to be accessible at 'base' sub-package."""

# Abstract classes to generate strategy and perform backtesting
from .entry_struct import EntryStruct
from .exit_struct import ExitStruct
from .gen_trades import GenTrades

# Pydantic object to record completed trade
from .stock_trade import StockTrade
from .stop_method import StopMethod
from .trade_signal import EntrySignal, ExitSignal

# Public interface
__all__ = [
    "EntryStruct",
    "ExitStruct",
    "GenTrades",
    "StopMethod",
    "EntrySignal",
    "ExitSignal",
    "StockTrade",
]
