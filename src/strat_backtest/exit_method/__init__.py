"""Import concrete implementation of 'ExitStruct' to be accessible
at 'exit_method' sub-package.

1. FIFOExit -> Reduce open positions via first-in-first-out.
2. LIFOExit -> Reduce open positions via last-in-Last-out.
3. HalfFIFOExit -> Reduce open positions by half via first-in-first out.
4. HalfLIFOExit -> Reduce open positions by half via last-in-first out.
5. TakeAllExit -> Close all open positions.
"""

from .fifo_exit import FIFOExit
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
]
