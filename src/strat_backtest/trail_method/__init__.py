"""Import concrete implementation of 'StopLoss' to be accessible
at 'stop_method' sub-package.

- FirstTrail -> Trailing Profit badsed on first open position.
"""

from .first_trail import FirstTrail

# Public interface
__all__ = [
    "FirstTrail",
]
