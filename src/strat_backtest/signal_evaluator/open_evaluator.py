"""Implementation of OpenEntry class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Open new position or close existing position on market open the next day.
"""

from typing import Any

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import Record, SigType


class OpenEvaluator(SignalEvaluator):
    """Open a new position at the market opening on next trading day.

    Args:
        sig_type (SigType):
            Either 'entry_signal' or 'exit_signal'.

    Attributes:
        sig_type (SigType):
            Either 'entry_signal' or 'exit_signal'.
    """

    def __init__(self, sig_type: SigType) -> None:
        super().__init__()
        self.sig_type = sig_type

    def evaluate(self, record: Record) -> dict[str, Any] | None:
        """Return dictionary (excluding ticker) required to open new position
        if conditions met."""

        # Get datetime, high, low, close and entry or exit signal from 'record'
        dt = record.get("date")
        sig = record.get(self.sig_type)

        # Validate if entry signal in 'record' matches with that in 'self.records'
        self._validate_sig(sig, self.sig_type)

        # Check if self.records is empty i.e. no prior 'buy' or 'sell' entry signal
        if not self.records:
            if sig != "wait":
                self.records.append(record)
            return None

        # Get existing entry signal, opening price and whether entry or exit price
        existing_sig = self._get_existing_sig(self.sig_type)
        open_price = record.get("open")
        price = f"{self.sig_type.split('_')[0]}_price"

        # Reset 'records' to empty list if 'entry_signal' != "wait" else update to
        # latest record
        self.records = [record] if sig != "wait" else []

        return {"dt": dt, self.sig_type: existing_sig, price: open_price}
