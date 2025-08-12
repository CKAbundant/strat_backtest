"""Abstract classes for generating completed trades."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Any

import pandas as pd

from strat_backtest.utils.constants import (
    CompletedTrades,
    EntryMethod,
    ExitMethod,
    ExitType,
    PriceAction,
    Record,
    SigEvalMethod,
    StopMethod,
    TrailMethod,
)
from strat_backtest.utils.file_utils import set_decimal_type
from strat_backtest.utils.pos_utils import (
    convert_to_decimal,
    get_class_instance,
    get_net_pos,
    get_std_field,
)
from strat_backtest.utils.utils import display_open_trades

if TYPE_CHECKING:
    from strat_backtest.base import SignalEvaluator, StopLoss, TrailProfit
    from strat_backtest.base.stock_trade import StockTrade
    from strat_backtest.utils import OpenTrades


@dataclass
class TradingConfig:
    """Core trading strategy configuration."""

    entry_struct: EntryMethod
    exit_struct: ExitMethod
    num_lots: int
    monitor_close: bool = True


@dataclass
class RiskConfig:
    """Risk management and stop loss configuration."""

    sig_eval_method: SigEvalMethod = "CloseEntry"
    trigger_percent: float | None = None
    percent_loss: float = 0.05
    stop_method: StopMethod = "no_stop"
    trail_method: TrailMethod = "no_trail"
    trigger_trail: float = 0.2
    step: float | None = None


class GenTrades(ABC):
    """Abstract class to generate completed trades for given strategy.

    Usage:
        >>> trading_cfg = TradingConfig(
                entry_struct, exit_struct, num_lots, monitor_close
            )
        >>> risk_cfg = RiskConfig(percent_loss, stop_method, trigger_trail, step)
        >>> trades = GenTrades(trading_cfg, risk_cfg)
        >>> df_trades, df_signals = trades.gen_trades(df_signals)

    Args:
        trading_cfg (TradingConfig):
            Instance of 'TradingConfig' dataclass containing 'entry_struct',
            'exit_struct', 'num_lots' and 'monitor_close' attributes.
        risk_cfg (RiskConfig):
            Instance of 'RiskConfig' dataclass containing 'percent_loss',
            'stop_method', 'trigger_trail' and 'step' attributes.

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

        # Get dictionary mapping
        self.module_paths = self._get_module_paths()

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
        self.init_sig_evaluator()

        # Create instance of 'FixedLoss' class if 'self.exit_struct' == 'FixedLoss'
        if self.exit_struct == "FixedExit":
            self.inst_cache[self.exit_struct] = get_class_instance(
                self.exit_struct, self.module_paths.get(self.exit_struct)
            )

    @abstractmethod
    def gen_trades(self, df_signals: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Generate DataFrame containing completed trades for given strategy.

        Args:
            df_signals (pd.DataFrame):
                DataFrame containing entry and exit signals for specific ticker.

        Returns:
            df_trades (pd.DataFrame):
                DataFrame containing completed trades.
            df_signals (pd.DataFrame):
                DataFrame containing updated exit signals price-related stops.
        """

        ...

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
        df = self._validate_req_cols(df)

        # Convert numeric type to Decimal
        df = set_decimal_type(df)
        completed_list = []

        # Intialize entry and exit signal evaluator if None
        sig_ent_eval = self.inst_cache["sig_ent_eval"]
        sig_ex_eval = self.inst_cache["sig_ex_eval"]

        for record in df.itertuples(index=True, name=None):
            # Create mapping for attribute to its values and check if end of DataFrame
            info = self.gen_mapping(record)
            is_end = info["idx"] >= len(df) - 1

            idx = info["idx"]
            dt = info["date"]

            print(f"\n\nidx : {idx}")
            print(f"dt : {dt}")
            print(f"sig_ent_eval.records : {sig_ent_eval.records}")
            print(f"sig_ex_eval.records : {sig_ex_eval.records}")
            print(f"net_pos : {get_net_pos(self.open_trades)}")

            # Close off all open positions at end of trading period
            # Skip creating new open positions after all open positions closed
            if is_end:
                completed_list = self.exit_all_end(completed_list, info)
                continue

            # Check whether to cut loss, take profit and open new position sequentially
            completed_list = self.check_stop_loss(completed_list, info)
            completed_list = self.check_profit(completed_list, info)
            completed_list = self.check_trailing_profit(completed_list, info)
            self.check_new_pos(ticker, info)

            print(
                f"self.inst_cache : \n\n{pformat(self.inst_cache, sort_dicts=False)}\n"
            )
            print(f"net_pos after update : {get_net_pos(self.open_trades)}")
            print(f"len(self.open_trades) : {len(self.open_trades)}")
            display_open_trades(self.open_trades)

            # print(
            #     "\n\nself.stop_info_list : "
            #     f"\n\n{pformat(self.stop_info_list, sort_dicts=False)}\n"
            # )

        # Append stop loss price and trailing price if available
        df_signals = self.append_info(df_signals, self.stop_info_list)
        df_signals = self.append_info(df_signals, self.trail_info_list)

        # Convert 'completed_list' to DataFrame; append 'ticker'
        df_trades = pd.DataFrame(completed_list)
        df_trades.to_parquet("sample_trades.parquet", index=False)

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

        print("Checking stop loss...")

        # Return 'completed_list' unamended if no net position or no stop loss set
        if len(self.open_trades) == 0 or self.stop_method == "no_stop":
            return completed_list

        if self.exit_struct == "FixedExit":
            fixed_exit = self.inst_cache.get("FixedExit")
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

        # No flipping of position for 'FixedExit' cos 'exit_signal' is always 'wait' i.e.
        # Exit position based strictly on pre-determined target profit
        if self.exit_struct == "FixedExit":
            fixed_exit = self.inst_cache.get("FixedExit")
            self.open_trades, completed_list = fixed_exit.check_all_profit(
                self.open_trades, completed_list, record
            )
            return completed_list

        entry_signal = record["entry_signal"]
        exit_signal = record["exit_signal"]

        ex_sig_eval = "OpenEvaluator" if self.flip else "sig_ex_eval"

        # Return 'completed_list' unamended if no open position or not exit
        # conditions met
        if (
            len(self.open_trades) == 0
            or (params := self.inst_cache[ex_sig_eval].evaluate(record)) is None
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
        # Note that entry and exit signals are only available at end of trading day. Hence
        # action can only be taken next trading day
        if exit_signal == entry_signal and exit_signal != "wait":
            self.flip = True

            if "OpenEvaluator" not in self.inst_cache:
                self.inst_cache["OpenEvaluator"] = get_class_instance(
                    "OpenEvaluator",
                    self.module_paths.get("OpenEvaluator"),
                    sig_type="exit_signal",
                )

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

        print("Checking trailing profit...")

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

        print("Checking new position...")

        # Evaluate incoming record and return parameters to create new position
        # if condition met
        if (params := self.inst_cache["sig_ent_eval"].evaluate(record)) is None:
            return None

        if self.entry_struct not in self.inst_cache:
            # Get initialized instance of concrete class implementation
            self.inst_cache[self.entry_struct] = get_class_instance(
                self.entry_struct,
                self.module_paths.get(self.entry_struct),
                num_lots=self.num_lots,
            )

        entry_instance = self.inst_cache.get(self.entry_struct)

        # Update 'self.open_trades' with new open position
        self.open_trades = entry_instance.open_new_pos(
            self.open_trades, ticker, **params
        )

        # Update profit and stop level for open position based on entry date
        if self.exit_struct == "FixedExit":
            if self.exit_struct not in self.inst_cache:
                self.inst_cache[self.exit_struct] = get_class_instance(
                    self.exit_struct, self.module_paths.get(self.exit_struct)
                )

            fixed_exit = self.inst_cache.get(self.exit_struct)
            fixed_exit.update_exit_levels(params["dt"], params["price"], record["stop"])

        if len(self.open_trades) == 0:
            raise ValueError("No open positions created!")

        return None

    def cal_trailing_profit(self, record: Record) -> Decimal | None:
        """Compute trailing profit price to protect profit."""

        if self.trail_method not in self.inst_cache:
            self.inst_cache[self.trail_method] = get_class_instance(
                self.trail_method,
                self.module_paths.get(self.trail_method),
                trigger_trail=self.trigger_trail,
                step=self.step,
            )

        trail_profit_inst = self.inst_cache.get(self.trail_method)

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

        # Get initialized instance of concrete class implementation
        if self.exit_struct not in self.inst_cache:
            self.inst_cache[self.exit_struct] = get_class_instance(
                self.exit_struct, self.module_paths.get(self.exit_struct)
            )

        exit_instance = self.inst_cache.get(self.exit_struct)

        # Update open trades and generate completed trades
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

        if "TakeAllExit" not in self.inst_cache:
            # Get initialized instance of concrete class implementation
            self.inst_cache["TakeAllExit"] = get_class_instance(
                "TakeAllExit", self.module_paths.get("TakeAllExit")
            )

        take_all_exit = self.inst_cache.get("TakeAllExit")

        # Update open trades and generate completed trades
        self.open_trades, completed_list = take_all_exit.close_pos(
            self.open_trades, dt, exit_price
        )

        if len(self.open_trades) != 0:
            raise ValueError("Open positions are not closed completely.")

        # Reset trailing profit attribute in self.inst_cache['trail_profit_inst']
        if self.trail_method in self.inst_cache:
            self.inst_cache[self.trail_method].reset_price_levels()

        # Reset 'records' attributes for 'sig_eval' since 'open_trades' is empty
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

        if self.stop_method not in self.inst_cache:
            self.inst_cache[self.stop_method] = get_class_instance(
                self.stop_method,
                self.module_paths.get(self.stop_method),
                percent_loss=self.percent_loss,
            )

        stop_loss_inst = self.inst_cache.get(self.stop_method)

        return stop_loss_inst.cal_exit_price(self.open_trades)

    def append_info(
        self,
        df_signals: pd.DataFrame,
        info_list: list[dict[str, str | datetime | Decimal]] | None = None,
    ) -> pd.DataFrame:
        """Convert 'info_list' (i.e. stop loss or trailing profit info) to DataFrame
        and append to 'df_signals'."""

        if len(info_list) == 0:
            return df_signals

        # Convert 'info_list' to DataFrame
        df_info = pd.DataFrame(info_list)

        # Ensure both 'date' column in 'df' and 'df_info' are time zone naive
        df_signals = self._set_naive_tz(df_signals)
        df_info = self._set_naive_tz(df_info)

        # Perform join via index
        df = df_signals.join(df_info)

        # Convert 'date' index to column
        df = df.reset_index()

        return df

    def gen_mapping(self, record: tuple[Any]) -> dict[str, Any]:
        """Generate mapping for record generated by 'itertuples' method."""

        # Record include row index and required fields
        fields = ["idx", *self.req_cols]

        return dict(zip(fields, record))

    def _set_naive_tz(self, data: pd.DataFrame) -> pd.DataFrame:
        """Set the 'data' column to be time zone naive and as index to
        faciliate join."""

        # Set 'date' column as index
        if "date" not in data.columns:
            raise ValueError("'date' column is not found.")

        df = data.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["date"] = df["date"].map(
            lambda dt: dt.replace(hour=0, minute=0, tzinfo=None)
        )
        df = df.set_index("date")

        return df

    def _get_module_paths(self, main_pkg: str = "strat_backtest") -> dict[str, str]:
        """Convert file path to package path that can be used as input to importlib.

        Args:
            script_path (str):
                Relative path to python script containig required module.
            main_pkg (str):
                Name of main package to generate module path
                (Default: "strat_backtest").

        Returns:
            module_info (dict[str, str]):
                Dictionary mapping each concrete class to module path.
        """

        # Get main package directory path
        main_pkg_path = Path(__file__).parents[1]

        # Get list of folder paths containin concrete implementation of 'EntryStruct',
        # 'ExitStruct', 'StopLoss' and 'TrailProfit' abstract class.
        folder_paths = [
            rel_path
            for rel_path in main_pkg_path.iterdir()
            if rel_path.is_dir()
            and rel_path.name not in {"base", "utils", "__pycache__"}
        ]

        module_info = {}

        # Iterate through contents of each folder path
        for folder in folder_paths:
            # Get all python scripts inside folder
            for file_path in folder.glob("*.py"):
                file_name = file_path.stem
                folder_name = folder.stem

                # Ignore __init__.py
                if file_name == "__init__":
                    continue

                # Get name of concrete class
                class_name = "".join(
                    part.upper() if part in {"fifo", "lifo"} else part.title()
                    for part in file_name.split("_")
                )

                module_info[class_name] = f"{main_pkg}.{folder_name}.{file_name}"

        return module_info

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

        dt = record["date"]
        open = convert_to_decimal(record["open"])
        close = convert_to_decimal(record["close"])
        low = convert_to_decimal(record["low"])
        high = convert_to_decimal(record["high"])

        # Get standard 'entry_action' from 'self.open_trades'; and stop price
        entry_action = get_std_field(self.open_trades, "entry_action")

        check_open_cond = (
            entry_action == "buy"
            and open <= trigger_price
            or entry_action == "sell"
            and open >= trigger_price
        )

        # List of exit conditions
        cond_list = [
            self.monitor_close and entry_action == "buy" and close <= trigger_price,
            self.monitor_close and entry_action == "sell" and close >= trigger_price,
            not self.monitor_close and entry_action == "buy" and low <= trigger_price,
            not self.monitor_close and entry_action == "sell" and high >= trigger_price,
        ]

        # Check if price triggered upon market opening
        if check_open_cond:
            completed_list.extend(self.exit_all(dt, open))
            trigger_status = Decimal("1")

        # Exit all open positions if any condition in 'cond_list' is true
        elif any(cond_list):
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

            self.inst_cache[key] = get_class_instance(
                self.sig_eval_method,
                self.module_paths.get(self.sig_eval_method),
                **input_params,
            )

    def _validate_req_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all columns in 'self.req_cols' are present in DataFrame; and return
        filtered DataFrame based on 'self.req_cols' columns."""

        # 'profit' and 'stop' columns are required if exit_struct is 'FixedExit'
        if self.exit_struct == "FixedExit":
            self.req_cols.extend(["stop"])

        not_available = [col for col in self.req_cols if col not in df.columns]

        if not_available:
            raise ValueError(f"{not_available} required columns are missing!")

        return df.loc[:, self.req_cols]
