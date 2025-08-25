"""Utility functions used for testing 'GenTrades'."""

from datetime import datetime
from decimal import Decimal
from typing import Any, TypeVar

import pandas as pd

from strat_backtest.base.gen_trades import GenTrades, RiskConfig, TradingConfig
from strat_backtest.utils.constants import (
    ClosedPositionResult,
    CompletedTrades,
    OpenTrades,
    PriceAction,
    Record,
)
from strat_backtest.utils.pos_utils import get_class_instance, get_std_field
from strat_backtest.utils.utils import convert_to_decimal
from tests.utils.test_utils import update_open_pos

# Create generic type variable 'T'
T = TypeVar("T")


class GenTradesTest(GenTrades):
    """Concrete implemenation for testing 'GenTrades' abstract class"""

    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        return pd.DataFrame(), pd.DataFrame()


def gen_testgentrades_inst(
    trading_cfg: TradingConfig, risk_cfg: RiskConfig, **kwargs: Any
) -> GenTradesTest:
    """Generate instance of 'GenTradesTest' class.

    Args:
        trading_cfg (TradingConfig):
            Instance of 'TradingConfig' StrEnum class.
        risk_cfg (RiskConfig):
            Instance of 'RiskConfig' StrEnum class.
        **kwargs (Any):
            Additional keyword arguments to set as attributes on the
            created instance. Only existing attributes will be modified.

    Returns:
        (GenTradesTest):
            Instance of 'GenTradesTest' class with specified configuration and
            any additional attributes set via kwargs.
    """

    # Create instance of 'GenTradesTest' with provided trading and risk config
    gen_trades = GenTradesTest(trading_cfg, risk_cfg)

    # Set attributes for valid keyword arguments
    for field, attribute in kwargs.items():
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
    price_type: str,
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
        price_type (str):
            Either "open" or "close" price.

    Returns:
        expected_list (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
    """

    # Assume exit signal is confirmed on previous trading day and close all positions at
    # current trading day open price
    completed_list.extend(
        gen_takeallexit_completed_list(open_trades, record["date"], record[price_type])
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
    percent_loss = convert_to_decimal(percent_loss)

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
        (Decimal): Stop price based on 'PercentLoss' method.
    """

    # Convert percent_loss to Decimal
    percent_loss = convert_to_decimal(percent_loss)

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
    params: dict[str, Any],
    completed_list: CompletedTrades,
    record: Record,
) -> tuple[CompletedTrades, dict[str, datetime | Decimal]]:
    """Generate expected 'completed_list' via 'exit_all_end" method
    at end of trading period.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'exit_all_end' method
    with the given parameters. Used for assertion comparisons in pytests.

    Args:
        params (dict[str, Any]):
            Dictionary containing parameters to intialize 'GenTradesTest'.
        completed_list (CompletedTrades):
            List of dictionaries containing completed trades info.
        record (Record):
            OHLCV info including entry and exit signal.

    Returns:
        (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
        (dict[str, datetime | Decimal]):
            Dictionary containing datetime, trigger price and whether triggered.
    """

    # Generate instance of 'GenTradesTest' with 'stop_method' == 'NearestLoss'
    test_inst = gen_testgentrades_inst(**params)

    # Convert percent_loss to Decimal
    percent_loss = convert_to_decimal(params["percent_loss"])

    # Generate expected 'completed_list
    stop_price = cal_nearestloss_stop_price(params["open_trades"], percent_loss)

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


def gen_check_profit_completed_list(
    open_trades: OpenTrades,
    completed_list: CompletedTrades,
    record: Record,
) -> ClosedPositionResult:
    """Generate expected 'completed_list' via 'check_profit" method.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'check_profit' method
    via 'FIFOExit' method with the given parameters. Used for assertion comparisons
    in pytests.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        completed_list (CompletedTrades):
            List of dictionaries containing completed trades info.
        record (Record):
            OHLCV info including entry and exit signal.

    Returns:
        expected_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        completed_list (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
    """

    # Assume exit signal occurs previous trading day and open position exited at opening
    # of current trading day
    dt = record["date"]
    exit_price = record["open"]

    expected_trades, expected_list = gen_take_profit_completed_list(
        open_trades, dt, exit_price
    )

    # Update existing 'completed_list'
    completed_list.extend(expected_list)

    return expected_trades, completed_list


def cal_trailing_price(
    open_trades: OpenTrades,
    record: Record,
    trigger_trail: float = 0.05,
    step: float | None = None,
) -> Decimal | None:
    """Compute trailing price based on 'FirstTrail' method given test open trades.

    This function creates the expected trailing price that should result from
    calling 'cal_trailing_profit' method for 'FirstTrail' trailing method.
    Used for assertion comparisons in pytests.

    Args:
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        record (Record):
            OHLCV info including entry and exit signal
        trigger_trail (Decimal):
            Percentage profit required to trigger trailing profit (Default: 0.05).
        step (float):
            If provided, amount of fixed increment step to trail profit.

    Returns:
        (Decimal | None): If available, trailing price based on 'FirstTrail' method.
    """

    # Ensure input parameters are decimal type
    high = convert_to_decimal(record["high"])
    low = convert_to_decimal(record["low"])
    trigger_trail = convert_to_decimal(trigger_trail)
    step = convert_to_decimal(step)

    if len(open_trades) == 0:
        return None

    # Use entry price for first open position as reference price
    first_price = open_trades[0].entry_price

    # Get standard 'entry_action' from 'self.open_trades'
    entry_action = get_std_field(open_trades, "entry_action")

    trigger_level = (
        first_price * (1 + trigger_trail)
        if entry_action == "buy"
        else first_price * (1 - trigger_trail)
    )

    # Check if current price has traded above the 'trigger_level' threshold
    excess = high - trigger_level if entry_action == "buy" else trigger_level - low

    if excess > 0:
        excess = (excess // step) * step if step else excess
        trailing_profit = (
            first_price + excess if entry_action == "buy" else first_price - excess
        )

        return round(trailing_profit, 2)

    # print(f"{excess=}")
    # print(f"first_price + excess : {first_price + excess}\n")

    return None


def gen_check_trailing_profit_completed_list(
    params: dict[str, Any],
    completed_list: CompletedTrades,
    record: Record,
) -> tuple[CompletedTrades, dict[str, datetime | Decimal]]:
    """Generate expected 'completed_list' via 'exit_all_end" method
    at end of trading period.

    This function creates the expected final state of completed trades
    (i.e. 'completed_list') that should result from calling 'exit_all_end' method
    with the given parameters. Used for assertion comparisons in pytests.

    Args:
        params (dict[str, Any]):
            Dictionary containing parameters to intialize 'GenTradesTest'.
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        completed_list (CompletedTrades):
            List of dictionaries containing completed trades info.
        record (Record):
            OHLCV info including entry and exit signal.

    Returns:
        (CompletedTrades):
            List of dictionaries containing completed trades info at end of
            trading period.
        (dict[str, datetime | Decimal]):
            Dictionary containing datetime, trigger price and whether triggered.
    """

    # Generate instance of 'GenTradesTest' with 'stop_method' == 'FirstTrail'
    test_inst = gen_testgentrades_inst(**params)

    # Generate expected 'completed_list
    trailing_price = cal_trailing_price(
        params["open_trades"], record, test_inst.trigger_trail, test_inst.step
    )

    # Update trailing profit
    if trailing_price is None:
        return completed_list, None

    # Check if stop loss triggered; and update 'completed_list' accordingly
    return test_inst._update_trigger_status(
        completed_list, record, trailing_price, exit_type="trail"
    )


def init_flip(
    test_inst: T,
    prev_record: Record,
    entry_sig: PriceAction,
    exit_sig: PriceAction,
) -> T:
    """Setup instance of 'OpenEvaluator' class in 'test_inst' class instance to flip position.

    - set 'flip' attribute to True
    - Create instance of 'OpenEvaluator' class and update to 'inst_cache' attribute
    - Update 'records' attribute for 'OpenEvaluator' instance.

    Args:
        test_inst (T):
            Class instance of 'GenTradesTest'.
        sample_gen_trades (pd.DataFrame):
            Sample DataFrame used for testing.
        entry_sig (PriceAction):
            Either 'buy' or 'sell' for 'entry_signal' in 'records' attribute.
        exit_sig (PriceAction):
            Either 'buy' or 'sell' for 'entry_signal' in 'records' attribute.

    Returns:
        test_inst (T):
            Class instance with updated 'OpenEvaluator' instance in
            'inst_cache' attribute.
    """

    # Set entry and exit signal for 'prev_record' to 'entry_sig' and 'exit_sig'
    # respectively
    prev_record["entry_signal"] = entry_sig
    prev_record["exit_signal"] = exit_sig

    # Set 'flip' flag to True
    test_inst.flip = True

    # Create instance of 'OpenEvaluator' class and update to 'inst_cache' attribute
    test_inst.inst_cache["OpenEvaluator"] = get_class_instance(
        "OpenEvaluator",
        test_inst.module_paths.get("OpenEvaluator"),
        sig_type="exit_signal",
    )

    # Update 'records' attribute of 'OpenEvaluator' instance
    test_inst.inst_cache["OpenEvaluator"].records = [prev_record]

    return test_inst
