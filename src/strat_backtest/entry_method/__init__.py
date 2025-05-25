"""Import concrete implementation of 'EntryStruct' to be accessible
at 'entry_method' sub-package.

1. MultiEntry -> Allow multiple open positions of fixed lottage.
2. MultiHalfEntry -> Reduce number of new open positions by half.
3. SingleEntry -> Allow only single open position at any time.
"""

from .multi_entry import MultiEntry
from .multi_half_entry import MultiHalfEntry
from .single_entry import SingleEntry

# Public interface
__all__ = [
    "MultiEntry",
    "MultiHalfEntry",
    "SingleEntry",
]
