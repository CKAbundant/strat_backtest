"""Test concrete implementation of 'StopLoss' abstract class

- FirstTrail - trailing profit level based on first open position
"""

from decimal import Decimal
from pprint import pformat

import pytest

from strat_backtest.trail_method import FirstTrail
from strat_backtest.utils.utils import convert_to_decimal, display_open_trades
from tests.utils.test_utils import get_latest_record


@pytest.mark.parametrize(
    "ref_price, error_type, exc_msg",
    [
        (None, ValueError, "'self.ref_price' is null value."),
        ("error", TypeError, "'self.ref_price' is not a valid numeric type."),
    ],
)
def test_cal_trigger_trail_level_error(ref_price, error_type, exc_msg):
    """Test if '_cal_trailing_profit' throws error if reference price (i.e. price used
    to compute trailing profit) is not available or wrong type"""

    entry_action = "buy"

    first_trail = FirstTrail()
    first_trail.ref_price = ref_price

    with pytest.raises(error_type) as exc_info:
        first_trail._cal_trigger_trail_level(entry_action)

    print(f"\n\n{str(exc_info.value)=}\n")

    assert exc_msg == str(exc_info.value)


@pytest.mark.parametrize(
    "entry_action, trigger_trail, expected_trigger_level",
    [
        ("buy", 0.1, 110),
        ("buy", 0.01, 101),
        ("buy", 0.2, 120),
        ("sell", 0.1, 90),
        ("sell", 0.01, 99),
        ("sell", 0.2, 80),
    ],
)
def test_cal_trigger_trail_level(entry_action, trigger_trail, expected_trigger_level):
    """Test if '_cal_trailing_profit' compute trigger trailing level correctly."""

    ref_price = Decimal("100")
    expected_trigger_level = convert_to_decimal(expected_trigger_level)

    first_trail = FirstTrail(trigger_trail=trigger_trail)
    first_trail.ref_price = ref_price
    trigger_trail_level = first_trail._cal_trigger_trail_level(entry_action)

    assert trigger_trail_level == expected_trigger_level


@pytest.mark.parametrize(
    "ref_price, trigger_trail_level, exc_msg",
    [
        (None, Decimal("110"), "'self.ref_price' is null value."),
        (Decimal("100"), None, "'self.trigger_trail_level' is null value."),
    ],
)
def test_cal_trailing_profit_error(ref_price, trigger_trail_level, exc_msg):
    """Test if '_cal_trailing_profit' throws error if 'self.ref_price' or
    'self.trailing_profit' is null value."""

    entry_action = "buy"
    record = {"high": Decimal("150"), "low": Decimal("80")}

    first_trail = FirstTrail()
    first_trail.ref_price = ref_price
    first_trail.trigger_trail_level = trigger_trail_level

    with pytest.raises(ValueError) as exc_info:
        first_trail._cal_trailing_profit(record, entry_action)

    print(f"\n\n{str(exc_info.value)=}\n")

    assert exc_msg == str(exc_info.value)


@pytest.mark.parametrize(
    "entry_action, step, existing_level, expected_trailing_profit",
    [
        ("buy", None, None, 143.3),
        ("buy", 2, None, 142),
        ("buy", 4, None, 140),
        ("buy", 9, None, 136),
        ("buy", None, 140, 143.3),
        ("buy", None, 143.3, 143.3),
        ("buy", None, 143.33, 143.33),
        ("sell", None, None, 88.8),
        ("sell", 2, None, 90),
        ("sell", 4, None, 92),
        ("sell", 9, None, 91),
        ("sell", None, 90, 88.8),
        ("sell", None, 88.8, 88.8),
        ("sell", None, 88.5, 88.5),
    ],
)
def test_cal_trailing_profit(
    entry_action, step, existing_level, expected_trailing_profit
):
    """Test if '_cal_trailing_profit' returns trailing profit level correctly‘"""

    ref_price = Decimal("100")
    trigger_trail = Decimal("0.1")
    record = {"high": Decimal("153.3"), "low": Decimal("78.8")}

    # Initialize instance of 'FirstTrail' and set attributes
    first_trail = FirstTrail(trigger_trail, step)
    first_trail.ref_price = ref_price
    first_trail.trailing_profit = convert_to_decimal(existing_level)
    first_trail.trigger_trail_level = (
        ref_price * (1 + trigger_trail)
        if entry_action == "buy"
        else ref_price * (1 - trigger_trail)
    )

    trailing_profit = first_trail._cal_trailing_profit(record, entry_action)
    print(f"\n\n{trailing_profit=}\n")

    assert trailing_profit == convert_to_decimal(expected_trailing_profit)


@pytest.mark.parametrize(
    "trigger_trail, step, expected_trailing_profit",
    [
        (0.01, None, 196.76),
        (0.05, None, 189.5),
        (0.1, None, None),
        (0.01, 2, 195.46),
        (0.01, 3, 196.46),
        (0.1, 5, None),
    ],
)
def test_cal_trail_price_firsttrail(
    open_trades, sample_gen_trades, trigger_trail, step, expected_trailing_profit
):
    """Test if 'cal_trail_price' method for 'FirstTrail' class compute trailing profit correctly."""

    record = get_latest_record(sample_gen_trades)

    first_trail = FirstTrail(trigger_trail, step)
    trailing_profit = first_trail.cal_trail_price(open_trades, record)
    print(f"{trailing_profit=}\n")

    assert trailing_profit == convert_to_decimal(expected_trailing_profit)
