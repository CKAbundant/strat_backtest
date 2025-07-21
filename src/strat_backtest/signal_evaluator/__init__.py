"""Import concrete implementation of 'SignalEvaluator' to be accessible
at 'signal_evaluator' sub-package.

1. BreakoutEntry -> Long when break above previous day high;
short when break below previous day low
"""

from .breakout_entry import BreakoutEntry
from .close_entry import CloseEntry
from .open_evaluator import OpenEvaluator

# Public interface
__all__ = [
    "BreakoutEntry",
    "CloseEntry",
    "OpenEvaluator",
]
