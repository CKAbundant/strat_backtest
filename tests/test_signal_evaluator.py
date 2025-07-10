"""Generate test for concrete implementation of 'SignalEvaluator'."""

from datetime import datetime
from decimal import Decimal
from pprint import pformat

import pytest

from strat_backtest.signal_evaluator import BreakoutEntry, CloseEntry, OpenEntry


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
            {
                "dt": datetime(2025, 4, 9),
                "ent_sig": "buy",
                "entry_price": Decimal("190.10"),
            },
        ),
        (
            "long_records",
            "long_success",
            0.002,
            {
                "dt": datetime(2025, 4, 9),
                "ent_sig": "buy",
                "entry_price": Decimal("190.47"),
            },
        ),
        (
            "short_records",
            "short_success",
            None,
            {
                "dt": datetime(2025, 4, 15),
                "ent_sig": "sell",
                "entry_price": Decimal("200.89"),
            },
        ),
        (
            "short_records",
            "short_success",
            0.002,
            {
                "dt": datetime(2025, 4, 15),
                "ent_sig": "sell",
                "entry_price": Decimal("200.5"),
            },
        ),
    ],
)
def test_breakoutentry_success(records, next_day, trigger_percent, expected, request):
    """Test if 'evaluate' method for 'BreakoutEntry' class generate the correct dictionary
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


@pytest.mark.parametrize(
    "next_day, expected",
    [
        (
            "long_success",
            {
                "dt": datetime(2025, 4, 9),
                "ent_sig": "buy",
                "entry_price": Decimal("198.59"),
            },
        ),
        ("no_entry", None),
    ],
)
def test_closeentry(next_day, expected, request):
    """Test if 'evaluate' method for 'CloseEntry' class returns None if no
    entry signal; and returns entry price == closing price if entry signal."""

    sig_eval = CloseEntry()
    next_day_record = request.getfixturevalue(next_day)

    output = sig_eval.evaluate(next_day_record)
    print(f"\n\n{output=}")
    print(f"{expected=}")
    print(f"\n{sig_eval.records=}")

    assert sig_eval.records == []
    assert output == expected


@pytest.mark.parametrize(
    "records, next_day, expected",
    [
        (
            "long_records",
            "long_success",
            {
                "dt": datetime(2025, 4, 9),
                "ent_sig": "buy",
                "entry_price": Decimal("171.72"),
            },
        ),
        (
            "short_records",
            "short_success",
            {
                "dt": datetime(2025, 4, 15),
                "ent_sig": "sell",
                "entry_price": Decimal("201.6"),
            },
        ),
    ],
)
def test_openentry_success(records, next_day, expected, request):
    """Test if 'evaluate' method for 'OpenEntry' class generate the correct dictionary
    to be used to generate new position."""

    sig_eval = OpenEntry()
    next_day_record = request.getfixturevalue(next_day)

    # Update records attribute
    sig_eval.records = request.getfixturevalue(records)

    print(f"\n\nsig_eval.records : {pformat(sig_eval.records, sort_dicts=False)}")
    print(f"\nnext_day_record : {pformat(next_day_record, sort_dicts=False)}")

    output = sig_eval.evaluate(next_day_record)
    print(f"\n\n{output=}")
    print(f"{expected=}")
    print(f"sig_eval.records after update : {sig_eval.records}")

    assert sig_eval.records == []
    assert output == expected


@pytest.mark.parametrize(
    "next_day", ["long_success", "long_fail", "short_success", "short_fail"]
)
def test_openentry_empty(next_day, request):
    """Test if 'evaluate' method for 'BreakoutEntry' class returns None if
    'self.records' is empty list."""

    sig_eval = OpenEntry()
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
