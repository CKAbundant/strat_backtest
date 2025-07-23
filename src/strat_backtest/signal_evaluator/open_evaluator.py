"""Implementation of OpenEntry class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Open new position or close existing position on market open the next day.
"""

from typing import Any

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import Record


class OpenEvaluator(SignalEvaluator):
    """Open a new position or close existing opn position at
    market opening on next trading day.
    """

    def evaluate(self, record: Record) -> dict[str, Any] | None:
        """Return dictionary (excluding ticker) required to open new position
        or close existing open position if conditions met."""

        # Get datetime, high, low, close and entry or exit signal from 'record'
        dt = record.get("date")
        sig = record.get(self.sig_type)

        # Validate empty records
        if self._validate_empty_records(sig, record):
            return None

        # Get existing entry or exit signal, opening price and entry or exit price
        existing_sig = self._get_existing_sig(self.sig_type)
        open_price = record.get("open")
        price = f"{self.sig_type.split('_')[0]}_price"

        # Reset 'records' to empty list if entry or exit signal != "wait" else update
        # to latest record
        self.records = [record] if sig != "wait" else []

        return {"dt": dt, self.sig_type: existing_sig, price: open_price}
