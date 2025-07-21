"""Implementation of BreakoutEntry class

- Concrete implementation of 'SignalEvaluator' abstract class.
- Enter long position or exit short position upon breaking out previous day high.
- Enter short position or exit long position upon breaking out previous day low.
"""

from decimal import Decimal
from typing import Any

from strat_backtest.base import SignalEvaluator
from strat_backtest.utils.constants import PriceAction, Record, SigType
from strat_backtest.utils.pos_utils import convert_to_decimal


class BreakoutEvaluator(SignalEvaluator):
    """Enter new position or close existing position if conditions met.

    - If entry signal is buy, enter long upon breaking above previous day high.
    - If entry signal is short, enter short upon breaking below previous day low.
    - If exit signal is buy, close short position if break above previous day high.
    - If exit signal is sell, close long position if break below previous day low.

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

    def __init__(
        self, sig_type: SigType, trigger_percent: Decimal | None = None
    ) -> None:
        super().__init__(sig_type)
        self.trigger_percent = convert_to_decimal(trigger_percent)

    def evaluate(self, record: Record) -> dict[str, Any] | None:
        """Return dictionary (excluding ticker) required to open new position
        if conditions are met."""

        # Get datetime, high, low, close and entry signal from 'record'
        dt = record.get("date")
        open = record.get("open")
        high = record.get("high")
        low = record.get("low")
        sig = record.get(self.sig_type)

        # Validate if entry signal in 'record' matches with that in 'self.records'
        self._validate_sig(sig, self.sig_type)

        # Check if self.records is empty i.e. no prior 'buy' or 'sell' entry signal
        if not self.records:
            if sig != "wait":
                self.records.append(record)
            return None

        # Get existing entry or exit signal, high and low of last record in 'self.records'
        existing_sig = self._get_existing_sig(self.sig_type)
        prev_high = self.records[-1].get("high")
        prev_low = self.records[-1].get("low")

        # Compute price to take action
        price = f"{self.sig_type.split('_')[0]}_price"
        action_price = self._cal_action_price(existing_sig, prev_high, prev_low, open)

        if (existing_sig == "buy" and high > prev_high) or (
            existing_sig == "sell" and low < prev_low
        ):
            # Reset 'records' to empty list if 'entry_signal' != "wait" else update to
            # latest record
            self.records = [record] if sig != "wait" else []

            return {
                "dt": dt,
                self.sig_type: existing_sig,
                price: action_price,
            }

        self.records.append(record)

        return None

    def _cal_action_price(
        self,
        sig: PriceAction,
        prev_high: Decimal,
        prev_low: Decimal,
        current_open: Decimal,
    ) -> Decimal:
        """Calculate action price based on 'breakout' and 'self.trigger_percent'.

        Args:
            entry_signal (PriceAction):
                Either "buy" to enter long or "sell" to enter short position.
            prev_high (Decimal):
                Previous day high.
            prev_low (Decimal):
                Previous day low.
            current_open (Decimal):
                Open price for current trading day.

        Returns:
            (Decimal): Entry price for breakout trades.
        """

        # Entry price is 0.01 (i.e. 1 bid higher) or (1 + self.trigger_percent) higher
        # for long position
        if sig == "buy":
            if prev_high < current_open:
                # Take action at opening if market gaps up
                action_price = current_open
            else:
                action_price = (
                    prev_high * (1 + self.trigger_percent)
                    if self.trigger_percent
                    else prev_high + Decimal("0.01")
                )

            return round(action_price, 2)

        if prev_low > current_open:
            # Take action at opening if market gaps down
            action_price = current_open

        else:
            # Entry price is 0.01 (i.e. 1 bid lower) or (1 - self.trigger_percent) lower
            # for short position
            action_price = (
                prev_low * (1 - self.trigger_percent)
                if self.trigger_percent
                else prev_low - Decimal("0.01")
            )
        return round(action_price, 2)
