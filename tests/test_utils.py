"""Utility functions used in test scripts."""

import random
from datetime import datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from strat_backtest.base.gen_trades import GenTrades, RiskConfig, TradingConfig
from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.utils.constants import (
    ClosedPositionResult,
    CompletedTrades,
    OpenTrades,
    PriceAction,
    Record,
)
from strat_backtest.utils.pos_utils import get_std_field


class TestGenTrades(GenTrades):
    """Concrete implemenation for testing 'GenTrades' abstract class"""

    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(), pd.DataFrame()


def gen_exit_record(
    df_sample: pd.DataFrame, ex_sig: PriceAction
) -> dict[str, str | Decimal]:
    """Generate dictionary with selected 'exit_signal'

    Args:
        df_sample (pd.DataFrame):
            Sample of signals DataFrame, which contains 'exit_signal' column.
        ex_sig (PriceAction):
            Either 'buy', 'sell' or 'wait'.

    Returns:
        (dict[str, str | Decimal]):
            Selected single record in 'df_sample' converted to dictionary.
    """

    # Filter 'df_sample' with 'entry_signal' and 'exit_signal' == 'wait'
    df_wait = df_sample.loc[
        (df_sample["entry_signal"] == "wait") & (df_sample["exit_signal"] == "wait"), :
    ].reset_index(drop=True)

    # Randomly select row with 'exit_signal' == 'wait'; and convert to dictionary
    random_idx = random.choice(list(df_wait.index))
    record = df_wait.iloc[random_idx, :].to_dict()

    # Set 'exit_signal' to desired value
    record["exit_signal"] = ex_sig

    return record


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
    for field, attribute in kwargs.items():
        if field not in vars(gen_trades):
            raise AttributeError(f"'{field}' is not a valid attribute for 'GenTrades'.")

        setattr(gen_trades, field, attribute)

    return gen_trades


def update_open_pos(
    trade: StockTrade, exit_dt: datetime | pd.Timestamp, exit_price: float
) -> StockTrade:
    """Update open position with exit datetime and price."""

    # Get 'exit_action' based on 'entry_action'
    exit_action = "sell" if trade.entry_action == "buy" else "buy"

    # Ensure 'exit_dt' is datetime type
    if isinstance(exit_dt, pd.Timestamp):
        exit_dt = exit_dt.to_pydatetime()

    trade.exit_datetime = exit_dt
    trade.exit_action = exit_action
    trade.exit_lots = trade.entry_lots
    trade.exit_price = Decimal(str(exit_price))

    return trade


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
        exit_price (float):
            Exit price to exit open position.

    Returns:
        expected_list (CompletedTrades):
            List of dictionaries containing completed trades info.
    """

    expected_list = []

    for open_pos in open_trades:
        # Update 'open_pos'
        pos = update_open_pos(open_pos.model_copy(), exit_dt, exit_price)

        # Convert to dictionary
        expected_list.append(pos.model_dump())

    return expected_list


def gen_exit_all_end_completed_list(
    open_trades: OpenTrades,
    completed_list: CompletedTrades,
    record: Record,
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
        record (Record):
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


def cal_percentloss_stop_price(
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


def cal_nearestloss_stop_price(
    open_trades: OpenTrades, percent_loss: float = 0.05
) -> Decimal:
    """Compute stop price based on 'NearestLoss' method given test open trades.

    This function creates the expected stop price that should result from
    calling 'cal_stop_price' method with the given parameters. Used for
    assertion comparisons in pytests.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        percent_loss (float):
            maximum percentage loss allowable.

    Returns:
        (Decimal): Stop price based on 'PercenLoss' method.
    """

    # Convert percent_loss to Decimal
    percent_loss = Decimal(str(percent_loss))

    # Entry action should be the same for all open positions
    entry_action = get_std_field(open_trades, "entry_action")

    # Calculate stop loss for each open position based on 'percent_loss'
    if entry_action == "buy":
        stop_list = [trade.entry_price * (1 - percent_loss) for trade in open_trades]

        return round(max(stop_list), 2)

    if entry_action == "sell":
        stop_list = [trade.entry_price * (1 + percent_loss) for trade in open_trades]

        return round(min(stop_list), 2)


def gen_check_stop_loss_completed_list(
    cfg: dict[str, TradingConfig | RiskConfig],
    open_trades: OpenTrades,
    completed_list: CompletedTrades,
    record: Record,
    percent_loss: float = 0.05,
) -> tuple[CompletedTrades, dict[str, datetime | Decimal]]:
    """Generate expected 'completed_list' via 'exit_all_end" method
    at end of trading period.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'exit_all_end' method
    with the given parameters. Used for assertion comparisons in pytests.

    Args:
        cfg (dict[TradingConfig, RiskConfig]):
            Dictionary mapping to instance of TradingConfig and RiskConfig.
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        completed_list (CompletedTrades):
            List of dictionaries containing completed trades info.
        record (Record):
            OHLCV info at end of trading period.
        percent_loss (float):
            maximum percentage loss allowable.

    Returns:
        (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
        (dict[str, datetime | Decimal]):
            Dictionary containing datetime, trigger price and whether triggered.
    """

    # Generate instance of 'TestGenTrades' with 'stop_method' == 'NearestLoss'
    test_inst = gen_testgentrades_inst(
        **cfg,
        stop_method="NearestLoss",
        open_trades=open_trades.copy(),
    )

    # Convert percent_loss to Decimal
    percent_loss = Decimal(str(percent_loss))

    # Generate expected 'completed_list
    stop_price = cal_nearestloss_stop_price(open_trades, percent_loss)

    # Check if stop loss triggered; and update 'completed_list' accordingly
    return test_inst._update_trigger_status(
        completed_list, record, stop_price, exit_type="stop"
    )


def gen_take_profit_completed_list(
    open_trades: OpenTrades,
    dt: datetime | pd.Timestamp,
    exit_price: float,
) -> ClosedPositionResult:
    """Generate expected 'completed_list' via 'take_profit" method.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'take_profit' method
    via 'FIFOExit' method with the given parameters. Used for assertion comparisons
    in pytests.

    Args:
        open_trades (OpenTrades):
                Deque list of StockTrade pydantic object to record open trades.
        dt (datetime | pd.Timestamp):
            Trade datetime object.
        exit_price (float):
            Exit price of stock ticker.

    Returns:
        open_trades (OpenTrades):
            Updated deque list of 'StockTrade' pydantic objects.
        completed_list (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
    """

    # First open position is exited
    first_trade = open_trades.popleft()

    # Update 'first_open' with 'dt' and 'exit_price'
    first_trade = update_open_pos(first_trade, dt, exit_price)

    return open_trades, [first_trade.model_dump()]
