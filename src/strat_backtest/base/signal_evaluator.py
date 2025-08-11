"""Abstract class to assess whether entry or exit signals
meet certain conditions over multiple days."""

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from strat_backtest.utils.constants import OpenTrades, PriceAction, Record, SigType


class SignalEvaluator(ABC):
    """Abstract class to assess whether entry or exit signals meet certain
    conditions over multiple days after triggering initial signals.

    - Example if buy signal is met, SignalEvaluator will check over next few
    days if market trades above previous day high before creating new position.

    Args:
        sig_type (SigType):
            Either 'entry_signal' or 'exit_signal'.

    Attributes:
        sig_type (SigType):
            Either 'entry_signal' or 'exit_signal'.
        records (list[Record]):
            List containing Record objects, which contain OHLCV, entry signal,
            exit signal and other relevant info
    """

    def __init__(self, sig_type: SigType) -> None:
        self.sig_type = sig_type
        self.records = []

    @abstractmethod
    def evaluate(self, record: Record) -> dict[str, Any] | None:
        """Return tuple required to open new position or close existing
        position if conditions are met.

        Args:
            record (Record):
                Dictionary containing OHLCV, entry, exit signal and
                other relevant info.

        Returns:
            (dict[str, Any] | None):
                If avaiable, dictionary containing fields required to create new
                position or close existing position.
        """

        ...

    def _validate_sig(self, sig: PriceAction, sig_type: str) -> None:
        """Validate if entry signal is consistent with entry signals in 'records' list.

        Args:
            sig (PriceAction): Either 'buy', 'sell' or 'wait'
            sig_type (str): Either 'entry_signal' or 'exit_signal'.

        Returns:
            None.
        """

        if sig not in {"buy", "sell", "wait"}:
            raise ValueError(f"{sig} is not a valid price action.")

        # 'self.records' is empty list or entry signal == "wait"
        if (existing_sig := self._get_existing_sig(sig_type)) is None or sig == "wait":
            return None

        if sig != existing_sig:
            raise ValueError(
                f"{sig_type} ({sig}) is not consistent with that in "
                f"'self.records' ({existing_sig})."
            )

        return None

    def _get_existing_sig(self, sig_type: str) -> PriceAction | None:
        """Get existing entry or exit signal in 'records' attribute i.e. whether
        signal is 'buy' or 'sell'. 'wait' is not considered."""

        # Return None if records is an empty list
        if not self.records:
            return None

        # Get set containing unique entry signals
        counter = Counter([record.get(sig_type) for record in self.records])
        sig_set = set(list(counter.keys()))

        # Both 'buy' and 'sell' should be present in 'self.records' concurrently
        if all(price_action in sig_set for price_action in ["buy", "sell"]):
            raise ValueError("Both buy and sell signals are present in 'self.records'.")

        unique_list = list(sig_set - {"wait", None})

        return unique_list[0] if unique_list else None

    def _validate_empty_records(self, sig: SigType, record: Record) -> bool:
        """Return True if 'records' is empty list. Append 'record' to 'records'
        if 'records' is not empty."""

        # Validate if entry signal in 'record' matches with that in 'self.records'
        self._validate_sig(sig, self.sig_type)

        # Check if self.records is empty i.e. no prior 'buy' or 'sell' entry signal
        if not self.records:
            if sig != "wait":
                self.records.append(record)
            return True

        return False

    def reset_records(self, open_trades: OpenTrades) -> None:
        """Set self.records to empty list if 'open_trades' is empty
        i.e. no open positions."""

        if len(open_trades) == 0:
            self.records = []
