"""Generate test for concrete implementation of 'SignalEvaluator'."""

from datetime import datetime
from decimal import Decimal
from pprint import pformat

import pytest

from strat_backtest.signal_evaluator import BreakoutEntry


@pytest.mark.parametrize(
    "records, price_action",
    [
        ("long_records", "test"),
        ("long_records", "sell"),
        ("short_records", "buy"),
        ("error_records", "buy"),
    ],
)
def test_validate_ent_sig(records, price_action, request):
    """Test if '_validate_ent_sig' throws a ValueError when entry signals are not
    consistent."""

    sig_eval = BreakoutEntry()
    sig_eval.records = request.getfixturevalue(records)

    with pytest.raises(ValueError):
        sig_eval._validate_ent_sig(price_action)


@pytest.mark.parametrize(
    "records, next_day, trigger_percent, expected",
    [
        (
            "long_records",
            "long_success",
            None,
            [datetime(2025, 4, 9), "buy", Decimal("190.10")],
        ),
        (
            "long_records",
            "long_success",
            0.002,
            [datetime(2025, 4, 9), "buy", Decimal("190.47")],
        ),
        (
            "short_records",
            "short_success",
            None,
            [datetime(2025, 4, 15), "sell", Decimal("200.89")],
        ),
        (
            "short_records",
            "short_success",
            0.002,
            [datetime(2025, 4, 15), "sell", Decimal("200.5")],
        ),
    ],
)
def test_breakoutentry_success(records, next_day, trigger_percent, expected, request):
    """Test if 'evaluate' method for 'BreakoutEntry' class generate the correct list
    to be used to generate new position."""

    sig_eval = BreakoutEntry(trigger_percent=trigger_percent)
    sig_eval.records = request.getfixturevalue(records)
    print(f"\n\nsig_eval.records : {pformat(sig_eval.records, sort_dicts=False)}")
    print(f"\nsig_eval.trigger_percent : {sig_eval.trigger_percent}")

    output = sig_eval.evaluate(request.getfixturevalue(next_day))
    print(f"\noutput : {output}")
    print(f"expected output : {expected}")
    print(
        f"\nsig_eval.records after trade confirmation : {pformat(sig_eval.records, sort_dicts=False)}\n\n"
    )

    assert sig_eval.records == []
    assert output == expected


@pytest.mark.parametrize(
    "next_day", ["long_success", "long_fail", "short_success", "short_fail"]
)
def test_breakoutentry_empty(next_day, request):
    """Test if 'evaluate' method for 'BreakoutEntry' class returns None if
    'self.records' is empty list."""

    sig_eval = BreakoutEntry()
    next_day_record = request.getfixturevalue(next_day)

    output = sig_eval.evaluate(next_day_record)
    print(f"\n\n{output=}")
    print(f"\n{sig_eval.records=}")

    assert output is None
    assert sig_eval.records == [next_day_record]

    # Amend 'entry_signal' in 'next_day_record' to 'wait'
    # Reset 'self.records' to empty list
    next_day_record["entry_signal"] = "wait"
    sig_eval.records = []

    _ = sig_eval.evaluate(next_day_record)
    assert sig_eval.records == []
