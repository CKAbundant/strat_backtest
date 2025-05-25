"""Import concrete implementation of 'StopLoss' to be accessible
at 'stop_method' sub-package.

- PercentLoss -> Stop loss based on pre-defined percent loss.
- NearestLoss -> Stop loss of open position that is nearest to current price.
- LatestLoss -> Stop loss of latest open position.
"""

from .latest_loss import LatestLoss
from .nearest_loss import NearestLoss
from .percent_loss import PercentLoss

# Public interface
__all__ = [
    "PercentLoss",
    "NearestLoss",
    "LatestLoss",
]
