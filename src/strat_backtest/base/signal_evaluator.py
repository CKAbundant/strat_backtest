"""Abstract class to assess whether entry or exit signals
meet certain conditions over multiple days."""

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from strat_backtest.utils.constants import PriceAction, Record


class SignalEvaluator(ABC):
    """Abstract class to assess whether entry or exit signals meet certain
    conditions over multiple days after triggering initial signals.

    - Example if buy signal is met, SignalEvaluator will check over next few
    days if market trades above previous day high before creating new position.

    Attributes:
        records (list[Record]):
            List containing Record objects, which contain OHLCV, entry signal,
            exit signal and other relevant info
    """

    def __init__(self) -> None:
        self.records = []

    @abstractmethod
    def evaluate(self, record: Record) -> tuple[Any]:
        """Return tuple required to open new position or close existing
        position if conditions are met.

        Args:
            record (Record):
                Dictionary containing OHLCV, entry, exit signal and
                other relevant info.

        Returns:
            (tuple[Any]):
                Tuple containing fields required to create new position or close
                existing position.
        """

        ...

    def _validate_ent_sig(self, ent_sig: PriceAction) -> None:
        """Validate if entry signal is consistent with entry signals in 'records' list."""

        # Return None if records is an empty list
        if not self.records:
            return None

        if ent_sig not in {"buy", "sell", "wait"}:
            raise ValueError(f"{ent_sig} is not a valid price action.")

        # Get set containing unique entry signals
        counter = Counter([record.get("entry_signal") for record in self.records])
        ent_set = set(list(counter.keys()))

        # Check if 'ent_sig' == "buy", then "sell" cannot appear in 'self.records'
        # and vice versa
        if (ent_sig == "buy" and "sell" in ent_set) or (
            ent_sig == "sell" and "buy" in ent_set
        ):
            raise ValueError(
                "entry signal is not consistent with that in 'self.records'."
            )

        return None
