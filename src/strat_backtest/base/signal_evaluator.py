"""Abstract class to assess whether entry or exit signals
meet certain conditions over multiple days."""

from abc import ABC, abstractmethod
from collections import Counter
from typing import Any

from strat_backtest.utils.constants import OpenTrades, PriceAction, Record


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

    def _validate_ent_sig(self, ent_sig: PriceAction) -> None:
        """Validate if entry signal is consistent with entry signals in 'records' list."""

        if ent_sig not in {"buy", "sell", "wait"}:
            raise ValueError(f"{ent_sig} is not a valid price action.")

        # 'self.records' is empty list or entry signal == "wait"
        if (
            existing_ent_sig := self._get_existing_ent_sig()
        ) is None or ent_sig == "wait":
            return None

        if ent_sig != existing_ent_sig:
            raise ValueError(
                f"entry signal ({ent_sig}) is not consistent with that in "
                f"'self.records' ({existing_ent_sig})."
            )

        return None

    def _get_existing_ent_sig(self) -> PriceAction | None:
        """Get existing entry signal i.e. whether entry signal is 'buy' or 'sell'.
        'wait' is not considered."""

        # Return None if records is an empty list
        if not self.records:
            return None

        # Get set containing unique entry signals
        counter = Counter([record.get("entry_signal") for record in self.records])
        ent_set = set(list(counter.keys()))

        # Both 'buy' and 'sell' should be present in 'self.records' concurrently
        if all(price_action in ent_set for price_action in {"buy", "sell"}):
            raise ValueError("Both buy and sell signals are present in 'self.records'.")

        unique_list = list(ent_set - {"wait", None})

        return unique_list[0] if unique_list else None

    def _reset_records(self, open_trades: OpenTrades) -> None:
        """Set self.records to empty list if 'open_trades' is empty
        i.e. no open positions."""

        if len(open_trades) == 0:
            self.records = []
