"""Generate test for concrete implementation of 'SignalEvaluator'."""

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


# def test_breakoutentry_evaluate(records):
#     """Test if"""
