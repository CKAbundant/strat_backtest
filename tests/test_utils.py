"""Utility functions used in test scripts."""

from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from strat_backtest.base.gen_trades import GenTrades, RiskConfig, TradingConfig
from strat_backtest.utils.constants import CompletedTrades, OpenTrades
from strat_backtest.utils.pos_utils import get_std_field


class TestGenTrades(GenTrades):
    """Concrete implemenation for testing 'GenTrades' abstract class"""

    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(), pd.DataFrame()


def gen_testgentrades_inst(
    trading_cfg: TradingConfig, risk_cfg: RiskConfig, **kwargs: Any
) -> TestGenTrades:
    """Generate instance of 'TestGenTrades' class.

    Args:
        trading_cfg (TradingConfig):
            Instance of 'TradingConfig' StrEnum class.
        risk_cfg (RiskConfig):
            Instance of 'RiskConfig' StrEnum class.
        **kwargs (Any):
            Additional keyword arguments to set as attributes on the
            created instance. Only existing attributes will be modified.

    Returns:
        (TestGenTrades):
            Instance of 'TestGenTrades' class with specified configuration and
            any additional attributes set via kwargs.
    """

    # Create instance of 'TestGenTrades' with provided trading and risk config
    gen_trades = TestGenTrades(trading_cfg, risk_cfg)

    # Set attributes for valid keyword arguments
    for (
        field,
        attribute,
    ) in kwargs.items():
        if field not in vars(gen_trades):
            raise AttributeError(f"'{field}' is not a valid attribute for 'GenTrades'.")

        setattr(gen_trades, field, attribute)

    return gen_trades


def gen_takeallexit_completed_list(
    open_trades: OpenTrades, exit_dt: datetime, exit_price: float
) -> CompletedTrades:
    """Generated expected completed list for 'open_trades' based on
    'TakeAllExit' method.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'exit_all' method
    with the given parameters. Used for assertion comparisons in pytest.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        exit_dt (datetime):
            Datetime object when open position is closed.

    Returns:
        expected_list (CompletedTrades):
            List of dictionaries containing completed trades info.
    """

    expected_list = []

    for open_pos in open_trades:
        # Create shallow copy of open position
        pos = open_pos.model_copy()

        # Update 'completed_pos' with exit info, ensuring positions
        # are properly closed
        pos.exit_datetime = exit_dt
        pos.exit_action = "sell" if pos.entry_action == "buy" else "buy"
        pos.exit_lots = pos.entry_lots
        pos.exit_price = exit_price

        expected_list.append(pos.model_dump())

    return expected_list


def gen_exit_all_end_completed_list(
    open_trades: OpenTrades,
    completed_list: CompletedTrades,
    record: dict[str, Decimal | datetime],
) -> CompletedTrades:
    """Generate expected 'completed_list' via 'exit_all_end" method
    at end of trading period.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'exit_all_end' method
    with the given parameters. Used for assertion comparisons in pytests.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        completed_list (CompletedTrades):
            Initial list of dictionaries containing completed trades info just
            before end of trading period.
        record (dict[str, Decimal | datetime]):
            OHLCV info at end of trading period.

    Returns:
        expected_list (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
    """

    completed_list.extend(
        gen_takeallexit_completed_list(open_trades, record["date"], record["close"])
    )

    return completed_list


def cal_percent_loss_stop_price(
    open_trades: OpenTrades, percent_loss: float = 0.05
) -> Decimal:
    """Compute stop price based on 'PercentLoss' method given test open trades.

    This function creates the expected stop price that should result from
    calling 'cal_stop_price' method with the given parameters. Used for
    assertion comparisons in pytests.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        percent_loss (float):
            maximum percentage loss allowable.

    Returns:
        (Decimal): Stop pricebased on 'PercenLoss' method.
    """

    # Convert percent_loss to Decimal
    percent_loss = Decimal(str(percent_loss))

    # Entry action should be the same for all open positions
    entry_action = get_std_field(open_trades, "entry_action")

    # Calculate average prices for open positions
    # Open positions are not partially filled, which simplifies calculation
    total_lots = sum(trade.entry_lots for trade in open_trades)
    av_price = (
        sum(trade.entry_price * trade.entry_lots for trade in open_trades) / total_lots
    )

    stop_price = (
        av_price * (1 - percent_loss)
        if entry_action == "buy"
        else av_price * (1 + percent_loss)
    )

    return round(stop_price, 2)
