"""Implementation of BreakoutEvaluator class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Enter long position or exit short position upon breaking out previous day high.
- Enter short position or exit long position upon breaking out previous day low.
"""

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import Record


class BreakoutEvaluator(SignalEvaluator):
    """Take action to either enter or exit position upon breakout.

    - Enter long position or exit short position upon breaking out previous day high.
    - Enter short position or exit long position upon breaking out previous day low.
    """

    def evaluate(record: Record) -> Record:
        """Return dictionary required to open new position or close existing
        position if conditions are met."""

        ...
