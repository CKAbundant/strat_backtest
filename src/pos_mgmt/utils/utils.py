"""Generic helper functions. For example:

- Manipulate DataFrame
- Format display via print
"""

from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pos_mgmt.base.stock_trade import StockTrade


def display_open_trades(open_trades: deque["StockTrade"]) -> None:
    """Omit 'days_held', 'profit_loss', 'percent_ret', 'daily_ret' and 'win' fields in StockTrade."""

    if len(open_trades) == 0:
        print("open_trades : []\n")
        return

    msg_list = []
    for trade in open_trades:
        entry_date_str = trade.exit_datetime.strftime("%Y-%m-%d")
        exit_date_str = trade.entry_datetime.strftime("%Y-%m-%d")
        exit_date = f"'{entry_date_str}'" if trade.exit_datetime else "None"
        exit_action = f"'{trade.exit_action}'" if trade.exit_action else "None"

        trade_str = (
            "   {\n"
            f"      ticker: '{trade.ticker}', "
            f"ent_dt: '{exit_date_str}', "
            f"ent_act: '{trade.entry_action}', "
            f"ent_lots: {trade.entry_lots}, "
            f"ent_price: {trade.entry_price}, "
            f"ex_dt: {exit_date}, "
            f"ex_act: {exit_action}, "
            f"ex_lots: {trade.exit_lots}, "
            f"ex_price: {trade.exit_price}"
            "\n   },"
        )
        msg_list.append(trade_str)

    msg = "\n".join(msg_list)

    print(f"open_trades : \n[\n{msg}\n]\n")


# Public Interface
__all__ = [
    "display_open_trades",
]
