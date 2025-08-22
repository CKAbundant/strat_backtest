"""Utilty function for testing concrete implementation of 'StopLoss' class."""

from decimal import Decimal

from strat_backtest.utils.constants import OpenTrades
from strat_backtest.utils.pos_utils import get_std_field
from strat_backtest.utils.utils import convert_to_decimal


def gen_stop_list(open_trades: OpenTrades, percent_loss: float = 0.2) -> list[Decimal]:
    """Generate list of stop prices based on 'entry_price' in 'open_trades'."""

    # Convert to Decimal type
    percent_loss = convert_to_decimal(percent_loss)

    # Extract entry price from 'open_trades'
    entry_list = [trade.entry_price for trade in open_trades]

    # Get standard entry action
    entry_action = get_std_field(open_trades, "entry_action")

    if entry_action == "buy":
        stop_list = [round(price * (1 - percent_loss), 2) for price in entry_list]
    else:
        stop_list = [round(price * (1 + percent_loss), 2) for price in entry_list]

    return stop_list


def cal_av_price(open_trades) -> Decimal:
    """Generate the average price based on existing open positions taking into
    consideration the number of lots."""

    total_investment = sum(
        trade.entry_price * trade.entry_lots for trade in open_trades
    )

    return total_investment / sum(trade.entry_lots for trade in open_trades)
