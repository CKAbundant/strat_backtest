"""Abstract classes for generating completed trades."""

from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, TypeVar

import pandas as pd

from strat_backtest.base.data_class import RiskConfig, TradingConfig
from strat_backtest.utils.constants import (
    CompletedTrades,
    ExitType,
    PriceAction,
    Record,
)
from strat_backtest.utils.file_utils import set_decimal_type
from strat_backtest.utils.gentrades_utils import (
    append_info,
    gen_mapping,
    get_module_paths,
    validate_req_cols,
)
from strat_backtest.utils.pos_utils import (
    gen_cond_list,
    get_class_instance,
    get_std_field,
)
from strat_backtest.utils.utils import convert_to_decimal

if TYPE_CHECKING:
    from strat_backtest.base import SignalEvaluator, StopLoss, TrailProfit
    from strat_backtest.base.stock_trade import StockTrade
    from strat_backtest.utils import OpenTrades
    from strat_backtest.utils.constants import (
        EntryMethod,
        ExitMethod,
        SigEvalMethod,
        StopMethod,
        TrailMethod,
    )

# Create generic type variable 'T'
T = TypeVar("T")


class GenTrades:
    """Abstract class to generate completed trades for given strategy.

    Usage:
        >>> trading_cfg = TradingConfig(
                entry_struct, exit_struct, num_lots, monitor_close
            )
        >>> risk_cfg = RiskConfig(
                percent_loss, stop_method, trigger_trail, step, time_period
            )
        >>> trades = GenTrades(trading_cfg, risk_cfg)
        >>> df_trades, df_signals = trades.gen_trades(df_signals)

    Args:
        trading_cfg (TradingConfig):
            Instance of 'TradingConfig' dataclass containing 'entry_struct',
            'exit_struct', 'num_lots' and 'monitor_close' attributes.
        risk_cfg (RiskConfig):
            Instance of 'RiskConfig' dataclass containing 'percent_loss',
            'stop_method', 'trigger_trail', 'step' and 'time_period' attributes.

    Attributes:
        entry_struct (EntryMethod):
            Whether to allow multiple open position ("MultiEntry") or single
            open position at a time ("SingleEntry").
        exit_struct (ExitMethod):
            Whether to apply "FIFOExit", "LIFOExit", "HalfFIFOExit", "HalfLIFOExit",
            or "TakeAllExit".
        sig_evaL_method (SigEvalMethod):
            Whether to apply "OpenEvaluator", or "BreakoutEvaluator".
        trigger_percent (Decimal):
            If provided, offset percentage for trade confirmation.
        num_lots (int):
            Number of lots to initiate new position each time (Default: 1).
        monitor_close (bool):
            Whether to monitor close price ("close") or both high and low price
            (Default: True).
        percent_loss (float):
            Percentage loss allowed for investment (Default: 0.05).
        stop_method (StopMethod):
            Exit method to generate stop price (Default: "no_stop").
        trail_method (TrailMethod):
            Exit method to generate trailing profit price (Default: "no_trail").
        trigger_trail (Decimal):
            Percentage profit required to trigger trailing profit (Default: 0.2).
        step (Decimal):
            If provided, percent profit increment to trail profit. If None,
            increment set to current high - trigger_trail_level.
        time_period (int | None):
            If provided, number of trading days to hold position before automatic
            exit via time-based mechanism. Works independently of exit_struct method.
            If None, no time-based exit applied.
        module_paths(dict[str, str]):
            Dictionary mapping name of concrete class to its module path.
        req_cols (list[str]):
            List of required columns to generate trades.
        open_trades (OpenTrades):
            Deque list of 'StockTrade' pydantic objects representing open positions.
        stop_info_list (list[dict[str, datetime | str | Decimal]]):
            List to record datetime, stop price and whether stop price is triggered.
        trail_info_list (list[dict[str, datetime | str | Decimal]]):
            List to record datetime, trail profit price and whether trailing profit
            is triggered.
        inst_cache (dict[str, Any]):
            Dictionary to cache instances of class imported dynamically via importlib.
        flip (bool):
            Whether to flip position (Default: False).
    """

    def __init__(
        self,
        trading_cfg: TradingConfig,
        risk_cfg: RiskConfig,
    ) -> None:
        # Trading configuration
        self.entry_struct = trading_cfg.entry_struct
        self.exit_struct = trading_cfg.exit_struct
        self.num_lots = trading_cfg.num_lots
        self.monitor_close = trading_cfg.monitor_close

        # Risk configuration
        self.sig_eval_method = risk_cfg.sig_eval_method or "OpenEvaluator"
        self.trigger_percent = convert_to_decimal(risk_cfg.trigger_percent)
        self.percent_loss = risk_cfg.percent_loss
        self.stop_method = risk_cfg.stop_method
        self.trail_method = risk_cfg.trail_method
        self.trigger_trail = convert_to_decimal(risk_cfg.trigger_trail)
        self.step = convert_to_decimal(risk_cfg.step)
        self.time_period = risk_cfg.time_period

        # Get dictionary mapping
        self.module_paths = get_module_paths()

        # Others
        self.req_cols = [
            "date",
            "open",
            "high",
            "low",
            "close",
            "entry_signal",
            "exit_signal",
        ]
        self.open_trades = deque()
        self.stop_info_list = []
        self.trail_info_list = []
        self.inst_cache = {}
        self.flip = False

    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Generate DataFrame containing completed trades for given strategy.

        Args:
            df_signals (pd.DataFrame):
                DataFrame containing entry and exit signals for specific ticker.
                Must include a 'ticker' column.

        Returns:
            df_trades (pd.DataFrame):
                DataFrame containing completed trades.
            df_signals (pd.DataFrame):
                DataFrame containing updated exit signals price-related stops.

        Raises:
            ValueError: If 'ticker' column is missing or contains multiple tickers.
        """
        # Validate ticker column exists
        if "ticker" not in df_signals.columns:
            raise ValueError("DataFrame must contain a 'ticker' column")

        # Extract unique ticker(s) and validate single ticker
        unique_tickers = df_signals["ticker"].unique()
        if len(unique_tickers) != 1:
            raise ValueError(
                f"DataFrame must contain exactly one ticker. Found: {unique_tickers}"
            )

        ticker = str(unique_tickers[0])

        # Delegate to existing iterate_df method
        return self.iterate_df(ticker, df_signals)

    def iterate_df(
        self, ticker: str, df_signals: pd.DataFrame
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Iterate through DataFrame containing buy and sell signals to
        populate completed trades.

        - Close off all open positions at end of trading period.
        - Check to cut loss for all open position.
        - Check to take profit.
        - Check to enter new position.
        - Update DataFrame with stop price and whether if triggered.

        Args:
            ticker (str):
                Stock ticker for back testing.
            df_signals (pd.DataFrame):
                DataFrame containing entry and exit signals.

        Returns:
            df_trades (pd.DataFrame):
                DataFrame containing completed trades.
            df_signals (pd.DataFrame):
                DataFrame containing updated exit signals based on price-related stops.
        """

        # Filter required columns i.e. date, open, high, low, close, entry
        # and exit signal
        df = df_signals.copy()
        df = validate_req_cols(df, self.req_cols, self.exit_struct)

        # Convert numeric type to Decimal
        df = set_decimal_type(df)
        completed_list = []

        # Intialize entry and exit signal evaluator
        self.init_sig_evaluator()

        for record in df.itertuples(index=True, name=None):
            # Create mapping for attribute to its values and check if end of DataFrame
            info = gen_mapping(record, self.req_cols)
            is_end = info["idx"] >= len(df) - 1

            # Check whether to cut loss, take profit and open new position sequentially
            completed_list = self.check_stop_loss(completed_list, info)
            completed_list = self.check_profit(completed_list, info)
            completed_list = self.check_trailing_profit(completed_list, info)

            # Close off all open positions at end of trading period
            # Skip creating new open positions after all open positions closed
            if is_end:
                completed_list = self.exit_all_end(completed_list, info)
            else:
                self.check_new_pos(ticker, info)

        # Append stop loss price and trailing price if available
        df_signals = append_info(df_signals, self.stop_info_list)
        df_signals = append_info(df_signals, self.trail_info_list)

        # Convert 'completed_list' to DataFrame; append 'ticker'
        df_trades = pd.DataFrame(completed_list)
        # df_trades.to_parquet("sample_trades.parquet", index=False)

        return df_trades, df_signals

    def exit_all_end(
        self,
        completed_list: CompletedTrades,
        record: Record,
    ) -> CompletedTrades:
        """Exit all open positions at end of testing/trading period.

        - Close off all position @ market closing if end of testing period.
        - No new postiion at end of testing period.

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (Record):
                Dictionary mapping required attributes to its values.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        if len(self.open_trades) == 0:
            # Return 'completed_list' unamended
            return completed_list

        # Close off all open positions at end of trading period
        completed_list.extend(self.exit_all(record["date"], record["close"]))

        return completed_list

    def check_stop_loss(
        self,
        completed_list: CompletedTrades,
        record: Record,
    ) -> CompletedTrades:
        """Check if stop loss condition met

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (Record):
                Dictionary mapping required attributes to its values.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        # print("Checking stop loss...")

        # Return 'completed_list' unamended if no net position or no stop loss set
        if len(self.open_trades) == 0 or self.stop_method == "no_stop":
            return completed_list

        # Check time-based exits first (independent of exit_struct)
        if self.time_period is not None:
            fixed_time_exit = self._get_inst_from_cache(
                "FixedTimeExit", time_period=self.time_period
            )
            self.open_trades, completed_list = fixed_time_exit.close_pos(
                self.open_trades, record["date"], record["close"]
            )
            # Continue to other exit checks even after time-based exits
            # (in case some positions remain open)

        if self.exit_struct == "FixedExit":
            fixed_exit = self._get_inst_from_cache(
                "FixedExit", monitor_close=self.monitor_close
            )
            self.open_trades, completed_list = fixed_exit.check_all_stop(
                self.open_trades, completed_list, record
            )
            return completed_list

        # Compute stop loss price based on 'self.stop_method'
        stop_price = self.cal_stop_price()

        # Check if stop loss triggered; and update 'completed_list' accordingly
        completed_list, trigger_info = self._update_trigger_status(
            completed_list, record, stop_price, exit_type="stop"
        )

        # Update 'self.stop_info_list' with trigger_info
        self.stop_info_list.append(trigger_info)

        return completed_list

    def check_profit(
        self,
        completed_list: CompletedTrades,
        record: Record,
    ) -> CompletedTrades:
        """Check whether take profit condition is met and update completed_list.

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (Record):
                Dictionary mapping required attributes to its values.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        # No flipping of position for 'FixedExit' cos 'exit_signal' is always 'wait'
        # i.e. Exit position based strictly on pre-determined target profit.
        if self.exit_struct == "FixedExit":
            fixed_exit = self._get_inst_from_cache(
                "FixedExit", monitor_close=self.monitor_close
            )
            self.open_trades, completed_list = fixed_exit.check_all_profit(
                self.open_trades, completed_list, record
            )
            return completed_list

        entry_signal = record["entry_signal"]
        exit_signal = record["exit_signal"]

        # Get 'OpenEvaluator' signal evaluator if 'flip' is set else use default
        # signal evaluator
        if self.flip:
            ex_sig_eval = self._get_inst_from_cache(
                "OpenEvaluator", sig_type="exit_signal"
            )
        else:
            ex_sig_eval = self.inst_cache["sig_ex_eval"]

        # Return 'completed_list' unamended if no open position or not exit
        # conditions met
        if (
            len(self.open_trades) == 0
            or (params := ex_sig_eval.evaluate(record)) is None
        ):
            return completed_list

        # Get standard 'entry_action' from 'self.open_trades'
        entry_action = get_std_field(self.open_trades, "entry_action")

        if exit_signal == entry_action:
            raise ValueError(
                f"Exit signal '{exit_signal}' is same as entry action '{entry_action}."
            )

        if self.flip:
            completed_list.extend(self.exit_all(params["dt"], params["exit_price"]))
        else:
            completed_list.extend(self.take_profit(**params))

        # Set 'self.flip' flag to true if exit and entry signal are same and not 'wait'
        # Note that entry and exit signals are only available at end of trading day.
        # Hence action can only be taken next trading day.
        if exit_signal == entry_signal and exit_signal != "wait":
            self.flip = True

        return completed_list

    def check_trailing_profit(
        self,
        completed_list: CompletedTrades,
        record: Record,
    ) -> CompletedTrades:
        """Check if stop loss condition met

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (Record):
                Dictionary mapping required attributes to its values.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        # print("Checking trailing profit...")

        # Return 'completed_list' unamended if no net position or
        # no trailing method set
        if len(self.open_trades) == 0 or self.trail_method == "no_trail":
            return completed_list

        # Update trailing profit
        if (trail_price := self.cal_trailing_profit(record)) is None:
            return completed_list

        # Check if trailing profit triggered; and update 'completed_list' accordingly
        completed_list, trigger_info = self._update_trigger_status(
            completed_list, record, trail_price, exit_type="trail"
        )

        # Update 'self.stop_info_list' with trigger_info
        self.trail_info_list.append(trigger_info)

        return completed_list

    def check_new_pos(
        self,
        ticker: str,
        record: Record,
    ) -> None:
        """Create new open position based on 'self.entry_struct' method.

        Args:
            ticker (str):
                Stock ticker to be traded.
            record (Record):
                Dictionary mapping required attributes to its values.

        Returns:
            None.
        """

        # print("Checking new position...")

        # Evaluate incoming record and return parameters to create new position
        # if condition met
        if (params := self.inst_cache["sig_ent_eval"].evaluate(record)) is None:
            return None

        # Update 'self.open_trades' with new open position
        entry_instance = self._get_inst_from_cache(
            self.entry_struct, num_lots=self.num_lots
        )
        self.open_trades = entry_instance.open_new_pos(
            self.open_trades, ticker, **params
        )

        # Update profit and stop level for open position based on entry date
        if self.exit_struct == "FixedExit":
            fixed_exit = self._get_inst_from_cache(
                "FixedExit", monitor_close=self.monitor_close
            )
            fixed_exit.update_exit_levels(
                params["dt"],
                params["entry_signal"],
                params["entry_price"],
                record["stop"],
            )

        if len(self.open_trades) == 0:
            raise ValueError("No open positions created!")

        return None

    def cal_trailing_profit(self, record: Record) -> Decimal | None:
        """Compute trailing profit price to protect profit."""

        trail_profit_inst = self._get_inst_from_cache(
            self.trail_method,
            trigger_trail=self.trigger_trail,
            step=self.step,
        )

        return trail_profit_inst.cal_trail_price(self.open_trades, record)

    def take_profit(
        self,
        dt: datetime | pd.Timestamp,
        exit_signal: PriceAction,
        exit_price: float,
    ) -> CompletedTrades:
        """Close existing open positions based on 'self.exit_struct' method.

        Args:
            dt (datetime | pd.Timestamp):
                Trade datetime object.
            exit_signal (PriceAction):
                Exit signal generated by 'ExitSignal' class either 'buy', 'sell'
                or 'wait'.
            exit_price (float):
                Exit price of stock ticker.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        # Get standard 'entry_action' from 'self.open_trades'
        entry_action = get_std_field(self.open_trades, "entry_action")

        if (
            entry_action is None
            or exit_signal == "wait"
            or (exit_signal in {"buy", "sell"} and exit_signal == entry_action)
        ):
            # No completed trades if exit signal is same as entry action
            return []

        # Update open trades and generate completed trades
        exit_instance = self._get_inst_from_cache(self.exit_struct)
        self.open_trades, completed_list = exit_instance.close_pos(
            self.open_trades, dt, exit_price
        )

        # Reset 'records' attributes for 'sig_eval' if 'open_trades' is empty
        if "sig_ent_eval" in self.inst_cache:
            self.inst_cache["sig_ent_eval"].reset_records(self.open_trades)
        if "sig_ex_eval" in self.inst_cache:
            self.inst_cache["sig_ex_eval"].reset_records(self.open_trades)

        return completed_list

    def exit_all(
        self,
        dt: datetime,
        exit_price: float,
    ) -> CompletedTrades:
        """Close all open positions via 'TakeAllExit.close_pos' method.

        Args:
            dt (datetime):
                Trade datetime object.
            exit_price (float):
                Exit price of stock ticker.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        take_all_exit = self._get_inst_from_cache("TakeAllExit")

        # Update open trades and generate completed trades
        self.open_trades, completed_list = take_all_exit.close_pos(
            self.open_trades, dt, exit_price
        )

        if len(self.open_trades) != 0:
            raise ValueError("Open positions are not closed completely.")

        # Reset trailing profit attribute in self.inst_cache['trail_profit_inst']
        if self.trail_method in self.inst_cache:
            self.inst_cache[self.trail_method].reset_price_levels()

        # Reset 'records' attributes for 'sig_eval' if 'open_trades' is empty
        if "sig_ent_eval" in self.inst_cache:
            self.inst_cache["sig_ent_eval"].reset_records(self.open_trades)
        if "sig_ex_eval" in self.inst_cache:
            self.inst_cache["sig_ex_eval"].reset_records(self.open_trades)

        # Reset 'self.flip' to False
        if "OpenEvaluator" in self.inst_cache:
            self.flip = False

        return completed_list

    def cal_stop_price(self) -> Decimal:
        """Compute price to trigger stop loss."""

        stop_loss_inst = self._get_inst_from_cache(
            self.stop_method, percent_loss=self.percent_loss
        )

        return stop_loss_inst.cal_exit_price(self.open_trades)

    # pylint: disable=too-many-locals
    def _update_trigger_status(
        self,
        completed_list: CompletedTrades,
        record: Record,
        trigger_price: Decimal,
        exit_type: ExitType,
    ) -> tuple[CompletedTrades, dict[str, datetime | Decimal]]:
        """Check if either trailing profit or stop loss price is triggered.

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (Record):
                Dictionary mapping required attributes to its values.
            trigger_price (Decimal):
                Either trailing profit or stop loss price.
            exit_type (ExitType):
                Either 'stop' or 'trail'.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            trigger_info (dict[str, datetime | Decimal]):
                Dictionary containing datetime, trigger price and whether triggered.
        """

        op = record.get("open")
        close = record.get("close")
        dt = record.get("date")

        # Get standard 'entry_action' from 'self.open_trades'; and stop price
        entry_action = get_std_field(self.open_trades, "entry_action")

        # Generate list of conditions for triggering action upon market
        # opening and after market open.
        open_cond, trigger_cond_list = gen_cond_list(
            record, entry_action, trigger_price, self.monitor_close
        )

        # Check if price triggered upon market opening
        if open_cond:
            completed_list.extend(self.exit_all(dt, op))
            trigger_status = Decimal("1")

        # Exit all open positions if any condition in 'cond_list' is true
        elif any(trigger_cond_list):
            # Actual exit price is closing price if monitor based on closing price
            # else trigger price
            exit_price = close if self.monitor_close else trigger_price

            completed_list.extend(self.exit_all(dt, exit_price))
            trigger_status = Decimal("1")

        else:
            trigger_status = Decimal("0")

        trigger_info = {
            "date": dt.to_pydatetime() if isinstance(dt, pd.Timestamp) else dt,
            f"{exit_type}_price": trigger_price,
            f"{exit_type}_triggered": trigger_status,
        }

        return completed_list, trigger_info

    def init_sig_evaluator(self) -> None:
        """Saved instance of concrete implementation of 'SignalEvaluator'
        abstract class to 'self.inst_cache' if not available."""

        params = {
            "sig_ent_eval": "entry_signal",
            "sig_ex_eval": "exit_signal",
        }

        for key, sig_type in params.items():
            input_params = {"sig_type": sig_type}

            if self.sig_eval_method == "BreakoutEvaluator":
                input_params.update({"trigger_percent": self.trigger_percent})

            _ = self._get_inst_from_cache(self.sig_eval_method, key, **input_params)

    def _get_inst_from_cache(
        self, class_name: str, key: str | None = None, **params: dict[str, Any]
    ) -> T:
        """Get class instance from 'self.inst_cache'. Generate new class instance
        if not available.

        Args:
            class_name (str):
                Name of class to create an instance.
            key (str):
                If provided, key will be used instead on class name in 'inst_cache'.
            **params (dict[str, Any]):
                Arbitrary Keyword input arguments to initialize class instance.
        """

        # Use 'key' instead of 'class_name' as key if 'key' is provided
        key = key or class_name

        # Create instance of 'FixedLoss' class if 'self.exit_struct' == 'FixedLoss'
        if key not in self.inst_cache:
            self.inst_cache[key] = get_class_instance(
                class_name, self.module_paths.get(class_name), **params
            )

        class_inst: T = self.inst_cache.get(key)

        return class_inst
