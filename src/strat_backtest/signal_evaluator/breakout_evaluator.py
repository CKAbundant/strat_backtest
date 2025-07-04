"""Implementation of BreakoutEvaluator class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Enter long position or exit short position upon breaking out previous day high.
- Enter short position or exit long position upon breaking out previous day low.
"""

from decimal import Decimal
from typing import Any

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import OpenTrades, PriceAction, Record
from strat_backtest.utils.pos_utils import convert_to_decimal


class BreakoutEntry(SignalEvaluator):
    """Take action to enter long or short depending on entry signal

    - If entry signal is buy, enter long upon breaking above previous day high.
    - If entry signal is short, enter short upon breaking below previous day low.

    Args:
        trigger_percent (Decimal | None):
            if provided, percentage for breakout confirmation. E.g. if trigger_percent
            == 0.02 and long, the entry price = 1.02 * previous day high. If not
            provided, then entry price = previous day high + 1 bid (i.e. 0.01).

    Attributes:
        trigger_percent (Decimal | None):
            if provided, percentage for breakout confirmation. E.g. if trigger_percent
            == 0.02 and long, the entry price = 1.02 * previous day high. If not
            provided, then entry price = previous day high + 1 bid (i.e. 0.01).

    """

    def __init__(self, trigger_percent: Decimal | None = None) -> None:
        super().__init__()
        self.trigger_percent = convert_to_decimal(trigger_percent)

    def evaluate(self, record: Record) -> list[Any] | None:
        """Return tuple (excluding ticker) required to open new position or close
        existing position if conditions are met."""

        # Get datetime, high, low, close and entry signal from 'record'
        dt = record.get("date")
        high = record.get("high")
        low = record.get("low")
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
        prev_high = self.records[-1].get("high")
        prev_low = self.records[-1].get("low")
        entry_price = self._cal_entry_price(existing_ent_sig, prev_high, prev_low)

        if (existing_ent_sig == "buy" and high > prev_high) or (
            existing_ent_sig == "sell" and low < prev_low
        ):
            # Reset records as long signal is confirmed
            self.records = []
            return [dt, existing_ent_sig, entry_price]

        # Append record to 'self.records' as entry signal is not confirmed
        self.records.append(record)

        return None

    def _reset_records(self, open_trades: OpenTrades) -> None:
        """Set self.records to empty list if 'open_trades' is empty
        i.e. no open positions."""

        if len(open_trades) == 0:
            self.records = []

    def _cal_entry_price(
        self, ent_sig: PriceAction, prev_high: Decimal, prev_low: Decimal
    ) -> Decimal:
        """Calculate entry price based on 'breakout' and 'self.trigger_percent'.

        Args:
            ent_sig (PriceAction):
                Either "buy" to enter long or "sell" to enter short position.
            prev_high (Decimal):
                Previous day high.
            prev_low (Decimal):
                Previous day low.

        Returns:
            (Decimal): Entry price for breakout trades.
        """

        # Entry price is 0.01 (i.e. 1 bid higher) or (1 + self.trigger_percent) higher
        # for long position
        if ent_sig == "buy":
            entry_price = (
                prev_high * (1 + self.trigger_percent)
                if self.trigger_percent
                else prev_high + Decimal("0.01")
            )
            return round(entry_price, 2)

        # Entry price is 0.01 (i.e. 1 bid lower) or (1 - self.trigger_percent) lower
        # for short position
        entry_price = (
            prev_low * (1 - self.trigger_percent)
            if self.trigger_percent
            else prev_low - Decimal("0.01")
        )
        return round(entry_price, 2)
