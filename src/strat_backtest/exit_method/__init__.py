"""Import concrete implementation of 'ExitStruct' to be accessible
at 'exit_method' sub-package.

1. FIFOExit -> Reduce open positions via first-in-first-out.
2. LIFOExit -> Reduce open positions via last-in-Last-out.
3. HalfFIFOExit -> Reduce open positions by half via first-in-first out.
4. HalfLIFOExit -> Reduce open positions by half via last-in-first out.
5. TakeAllExit -> Close all open positions.
6. FixedExit -> Close specific position based on entry date.
7. FixedTimeExit -> Close positions after fixed time period.
"""

from .fifo_exit import FIFOExit
from .fixed_exit import FixedExit
from .fixed_time_exit import FixedTimeExit
from .half_fifo_exit import HalfFIFOExit
from .half_lifo_exit import HalfLIFOExit
from .lifo_exit import LIFOExit
from .take_all_exit import TakeAllExit

# Public interface
__all__ = [
    "FIFOExit",
    "LIFOExit",
    "HalfFIFOExit",
    "HalfLIFOExit",
    "TakeAllExit",
    "FixedExit",
    "FixedTimeExit",
]
