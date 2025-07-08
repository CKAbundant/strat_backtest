"""Implementation of OpenEvaluator class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Open new position or close existing position on market open the next day.
"""

from typing import Any

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import Record


class OpenEntry(SignalEvaluator):
    """Open a new position at the market opening on next trading day i.e.
    entry price = open price."""

    def evaluate(self, record: Record) -> dict[str, Any] | None:
        """Return dictionary (excluding ticker) required to open new position
        if conditions met."""

        # Get datetime, high, low, close and entry signal from 'record'
        dt = record.get("date")
        ent_sig = record.get("entry_signal")

        # Validate if entry signal in 'record' matches with that in 'self.records'
        self._validate_ent_sig(ent_sig)

        # Check if self.records is empty i.e. no prior 'buy' or 'sell' entry signal
        if not self.records:
            if ent_sig != "wait":
                self.records.append(record)
            return None

        # Get existing entry signal, high and low of last record in 'self.records'
        existing_ent_sig = self._get_existing_ent_sig()
        entry_price = self.records[-1].get("open")

        # Append record to 'self.records' as entry signal is not confirmed
        self.records = []

        return {"dt": dt, "ent_sig": existing_ent_sig, "entry_price": entry_price}
