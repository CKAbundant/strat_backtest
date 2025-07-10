"""Implementation of CloseEvaluator class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Open new position or close existing position.
"""

from typing import Any

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import Record


class CloseEntry(SignalEvaluator):
    """Open a new position at the market closing i.e. entry price = closing price."""

    def evaluate(self, record: Record) -> dict[str, Any] | None:
        """Return dictionary (excluding ticker) required to open new position
        if conditions met."""

        # Get datetime, entry price (i.e. close) and entry signal from 'record'
        dt = record.get("date")
        entry_price = record.get("close")
        ent_sig = record.get("entry_signal")

        # Ensure 'self.records' is empty list
        self.records = []

        if ent_sig not in {"buy", "sell"}:
            # Exit since no entry signal no entry signal
            return None

        return {"dt": dt, "ent_sig": ent_sig, "entry_price": entry_price}
