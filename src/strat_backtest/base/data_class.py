"""Data Class for initializing 'GenTrades' class"""

from dataclasses import dataclass

from strat_backtest.utils.constants import (
    EntryMethod,
    ExitMethod,
    SigEvalMethod,
    StopMethod,
    TrailMethod,
)


@dataclass
class TradingConfig:
    """Core trading strategy configuration."""

    entry_struct: EntryMethod
    exit_struct: ExitMethod
    num_lots: int
    monitor_close: bool = True


@dataclass
class RiskConfig:
    """Risk management and stop loss configuration."""

    sig_eval_method: SigEvalMethod = "CloseEntry"
    trigger_percent: float | None = None
    percent_loss: float = 0.05
    stop_method: StopMethod = "no_stop"
    trail_method: TrailMethod = "no_trail"
    trigger_trail: float = 0.2
    step: float | None = None
