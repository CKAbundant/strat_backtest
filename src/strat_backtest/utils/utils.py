"""Generic helper functions. For example:

- Manipulate DataFrame
- Format display via print
"""

from decimal import Decimal
from typing import Any

from strat_backtest.utils.constants import OpenTrades


def display_open_trades(open_trades: OpenTrades, var_name: str | None = None) -> None:
    """Omit 'days_held', 'profit_loss', 'percent_ret', 'daily_ret'
    and 'win' fields in StockTrade."""

    # Set name of variable as 'open_trades' if not provided
    var_name = var_name or "open_trades"

    if len(open_trades) == 0:
        print(f"{var_name} : []\n")
        return None

    msg_list = []
    for trade in open_trades:
        entry_date = trade.entry_datetime.strftime("%Y-%m-%d")
        exit_date = (
            f"'{trade.exit_datetime.strftime('%Y-%m-%d')}'"
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

    print(f"\n\n{var_name} : \n[\n{msg}\n]\n")

    return None


def convert_to_decimal(var: Any | None, dec_pl: int | None = None) -> Decimal | None:
    """Convert 'var' to Decimal type if numeric type.

    Args:
        var (Any): Variable to be converted to Decimal if numeric type.
        dec_pl (int): Number of decimal places to round numeric variable.

    Returns:
        (Decimal | None):
            If available, numeric variable converted to Decimal else unchanged.
    """

    if var is None:
        return None

    if not isinstance(var, (int, float, Decimal)):
        return var

    # Convert numeric type to Decimal type
    decimal_var = var if dec_pl is None else round(var, dec_pl)

    return Decimal(str(decimal_var))


# Public Interface
__all__ = [
    "display_open_trades",
    "convert_to_decimal",
]
