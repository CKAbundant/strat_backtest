"""Generic helper functions. For example:

- Manipulate DataFrame
- Format display via print
"""

from strat_backtest.utils.constants import OpenTrades


def display_open_trades(open_trades: OpenTrades) -> None:
    """Omit 'days_held', 'profit_loss', 'percent_ret', 'daily_ret'
    and 'win' fields in StockTrade."""

    if len(open_trades) == 0:
        print("open_trades : []\n")
        return None

    msg_list = []
    for trade in open_trades:
        entry_date = trade.entry_datetime.strftime("%Y-%m-%d")
        exit_date = (
            f"\"{trade.exit_datetime.strftime('%Y-%m-%d')}\""
            if trade.exit_datetime
            else "None"
        )
        exit_action = f"'{trade.exit_action}'" if trade.exit_action else "None"

        trade_str = (
            "   {\n"
            f"      ticker: '{trade.ticker}', "
            f"ent_dt: '{entry_date}', "
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

    return None


# Public Interface
__all__ = [
    "display_open_trades",
]
