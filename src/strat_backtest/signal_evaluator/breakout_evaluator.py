"""Implementation of BreakoutEvaluator class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Enter long position or exit short position upon breaking out previous day high.
- Enter short position or exit long position upon breaking out previous day low.
"""

from typing import Any

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import Record


class BreakoutEntry(SignalEvaluator):
    """Take action to enter long or short depending on entry signal

    - If entry signal is buy, enter long upon breaking above previous day high.
    - If entry signal is short, enter short upon breaking below previous day low.
    """

    def evaluate(self, record: Record) -> tuple[Any]:
        """Return tuple required to open new position or close existing
        position if conditions are met."""

        # Validate if entry signal in 'record' matches with that in 'self.records'
        self._validate_ent_sig(record["entry_signal"])
