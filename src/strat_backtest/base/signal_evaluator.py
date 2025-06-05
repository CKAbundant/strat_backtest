"""Abstract class to assess whether entry or exit signals
meet certain conditions over multiple days."""

from abc import ABC, abstractmethod
from decimal import Decimal

from strat_backtest.utils.constants import Record


class SignalEvaluator(ABC):
    """Abstract class to assess whether entry or exit signals meet certain
    conditions over multiple days after triggering initial signals.

    - Example if buy signal is met, SignalEvaluator will check over next few
    days if market trades above previous day high before creating new position.

    Attributes:
        counter (int):
            Counter to validate multiple entry/exit signals.
        records (dict[str, Record]):
            Dictionary mapping Record object, which contain OHLCV, entry signal,
            exit signal and other relevant info.
    """

    def __init__(self) -> None:
        self.counter = 0
        self.records = {}

    @abstractmethod
    def evaluate(record: Record) -> Record:
        """Return dictionary required to open new position or close existing
        position if conditions are met.

        Args:
            record (Record):
                Dictionary containing OHLCV, entry, exit signal and
                other relevant info.

        Returns:
            (Record):
                Updated dictionary containing required information to create new
                position or close existing position i.e. ticker, datetime, entry
                /exit signals and entry/exit price.
        """

        ...
