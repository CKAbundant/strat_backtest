"""Generate test for concrete implementation of 'SignalEvaluator'."""

import pytest

from strat_backtest.signal_evaluator import BreakoutEntry


def test_validate_ent_sig(records):
    """Test if '_validate_ent_sig' throws a ValueError when entry signals are not
    consistent."""

    sig_eval = BreakoutEntry()
    sig_eval.records = records

    assert sig_eval.evaluate({"entry_signal": "wait"}) is None

    with pytest.raises(ValueError):
        sig_eval.evaluate({"entry_signal": "sell"})
