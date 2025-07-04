"""Generate test for concrete implementation of 'SignalEvaluator'."""

import pytest

from strat_backtest.signal_evaluator import BreakoutEntry


@pytest.mark.parametrize("price_action", ["test", "sell"])
def test_validate_ent_sig(records, price_action):
    """Test if '_validate_ent_sig' throws a ValueError when entry signals are not
    consistent."""

    sig_eval = BreakoutEntry()
    sig_eval.records = records

    with pytest.raises(ValueError):
        sig_eval._validate_ent_sig(price_action)
