"""Test concrete implementation of 'StopLoss' abstract class

- LatestLoss - Stop loss based on latest position
- NearestLoss - Stop loss based on position that is nearest to current price
- PercentLoss - Stop loss based on percent loss of all open positions
"""

from collections import deque

import pytest

from strat_backtest.stop_method import LatestLoss, NearestLoss, PercentLoss
from strat_backtest.utils.pos_utils import get_std_field
from strat_backtest.utils.utils import convert_to_decimal, display_open_trades
from tests.utils.test_stop_method_utils import cal_av_price, gen_stop_list


@pytest.mark.parametrize(
    "error, exc_msg",
    [
        ("no_open", "'open_trades' cannot be empty."),
        ("inconsistent_entry", "'entry_action' field is not consistent."),
    ],
)
def test_latestloss_error(open_trades, error, exc_msg):
    """Test if stop loss is computed based on nearest position."""

    latest_loss = LatestLoss()

    if error == "no_open":
        open_trades = deque()
    else:
        open_trades[1].entry_action = "sell"

    with pytest.raises(ValueError) as exc_info:
        latest_loss.cal_exit_price(open_trades)

    display_open_trades(open_trades)
    print(f"{str(exc_info.value)=}")

    assert exc_msg == str(exc_info.value)


@pytest.mark.parametrize("percent_loss", [0.1, 0.2, 0.3])
def test_latestloss(open_trades, percent_loss):
    """Test if stop loss is computed based on nearest position."""

    latest_loss = LatestLoss(percent_loss=percent_loss)
    stop_price = latest_loss.cal_exit_price(open_trades)

    # Generate list of stop prices based on 'open_trades'
    expected_stop_list = gen_stop_list(open_trades, percent_loss)

    display_open_trades(open_trades)
    print(f"{stop_price=}")
    print(f"{expected_stop_list=}\n")

    assert stop_price == expected_stop_list[-1]


@pytest.mark.parametrize(
    "error, exc_msg",
    [
        ("no_open", "'open_trades' cannot be empty."),
        ("inconsistent_entry", "'entry_action' field is not consistent."),
    ],
)
def test_nearestloss_error(open_trades, error, exc_msg):
    """Test if stop loss is computed based on nearest position."""

    nearest_loss = NearestLoss()

    if error == "no_open":
        open_trades = deque()
    else:
        open_trades[1].entry_action = "sell"

    with pytest.raises(ValueError) as exc_info:
        nearest_loss.cal_exit_price(open_trades)

    display_open_trades(open_trades)
    print(f"{str(exc_info.value)=}")

    assert exc_msg == str(exc_info.value)


@pytest.mark.parametrize("percent_loss", [0.1, 0.2, 0.3])
def test_nearestloss(open_trades, percent_loss):
    """Test if stop loss is computed based on nearest position."""

    nearest_loss = NearestLoss(percent_loss=percent_loss)
    stop_price = nearest_loss.cal_exit_price(open_trades)

    # Generate list of stop prices based on 'open_trades'
    expected_stop_list = gen_stop_list(open_trades, percent_loss)

    # Get standard entry action
    entry_action = get_std_field(open_trades, "entry_action")

    display_open_trades(open_trades)
    print(f"{stop_price=}")
    print(f"{expected_stop_list=}\n")

    expected_stop_price = (
        max(expected_stop_list) if entry_action == "buy" else min(expected_stop_list)
    )

    assert stop_price == expected_stop_price


@pytest.mark.parametrize(
    "error, exc_msg",
    [
        ("no_open", "'open_trades' cannot be empty."),
        ("inconsistent_entry", "'entry_action' field is not consistent."),
    ],
)
def test_percentloss_error(open_trades, error, exc_msg):
    """Test if stop loss is computed based on nearest position."""

    percent_loss = PercentLoss()

    if error == "no_open":
        open_trades = deque()
    else:
        open_trades[1].entry_action = "sell"

    with pytest.raises(ValueError) as exc_info:
        percent_loss.cal_exit_price(open_trades)

    display_open_trades(open_trades)
    print(f"{str(exc_info.value)=}")

    assert exc_msg == str(exc_info.value)


@pytest.mark.parametrize("percentage_loss", [0.1, 0.2, 0.3])
def test_percentloss(open_trades, percentage_loss):
    """Test if stop loss is computed based on total investment portfolio."""

    percentage_loss = convert_to_decimal(percentage_loss)

    percent_loss = PercentLoss(percent_loss=percentage_loss)
    stop_price = percent_loss.cal_exit_price(open_trades)

    # Generate list of stop prices based on 'open_trades'
    av_price = cal_av_price(open_trades)

    # Get standard entry action
    entry_action = get_std_field(open_trades, "entry_action")

    # Compute expected stop loss based on 'av_price' i.e. average price of
    # overall portfolio
    expected_stop_price = (
        round(av_price * (1 - percentage_loss), 2)
        if entry_action == "buy"
        else round(av_price * (1 + percentage_loss), 2)
    )

    # display_open_trades(open_trades)
    print(f"\n\n{stop_price=}")
    print(f"{expected_stop_price=}\n")

    assert stop_price == expected_stop_price
