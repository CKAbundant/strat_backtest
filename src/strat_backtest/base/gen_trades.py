"""Abstract classes for generating completed trades."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pandas as pd

from strat_backtest.utils.constants import (
    CompletedTrades,
    EntryMethod,
    ExitMethod,
    ExitType,
    PriceAction,
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
    from strat_backtest.base import StopLoss, TrailProfit
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

    percent_loss: float = 0.05
    stop_method: ExitMethod = "no_stop"
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
        num_lots (int):
            Number of lots to initiate new position each time (Default: 1).
        monitor_close (bool):
            Whether to monitor close price ("close") or both high and low price
            (Default: True).
        percent_loss (float):
            Percentage loss allowed for investment (Default: 0.05).
        stop_method (ExitMethod):
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
        stop_loss_inst (StopLoss):
            Instance of 'StopLoss' class.
        trail_profit_inst (TrailProfit):
            Instance of 'TrailProfit' class.
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
            "high",
            "low",
            "close",
            "entry_signal",
            "exit_signal",
        ]
        self.open_trades = deque()
        self.stop_info_list = []
        self.trail_info_list = []
        self.stop_loss_inst = None
        self.trail_profit_inst = None

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

        # Filter required columns i.e. date, high, low, close, entry and exit signal
        df = df_signals.copy()
        df = df.loc[:, self.req_cols]

        # Convert numeric type to Decimal
        df = set_decimal_type(df)
        completed_list = []

        for record in df.itertuples(index=True, name=None):
            # Create mapping for attribute to its values and check if end of DataFrame
            info = self.gen_mapping(record)
            is_end = info["idx"] >= len(df) - 1

            idx = info["idx"]
            dt = info["date"]
            close = info["close"]
            ent_sig = info["entry_signal"]
            ex_sig = info["exit_signal"]

            print(f"idx : {idx}")
            print(f"dt : {dt}")
            print(f"close : {close}")
            print(f"ent_sig : {ent_sig}")
            print(f"ex_sig : {ex_sig}")
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

            print(f"net_pos after update : {get_net_pos(self.open_trades)}")
            print(f"len(self.open_trades) : {len(self.open_trades)}")
            display_open_trades(self.open_trades)

        # Append stop loss price and trailing price if available
        df_signals = self.append_info(df_signals, self.stop_info_list)
        df_signals = self.append_info(df_signals, self.trail_info_list)

        # Convert 'completed_list' to DataFrame; append 'ticker'
        df_trades = pd.DataFrame(completed_list)

        return df_trades, df_signals

    def exit_all_end(
        self,
        completed_list: CompletedTrades,
        record: dict[str, Decimal | datetime],
    ) -> CompletedTrades:
        """Exit all open positions at end of testing/trading period.

        - Close off all position if end of testing period.
        - No new postiion at end of testing period.

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (dict[str, Decimal | datetime]):
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
        record: dict[str, Decimal | datetime],
    ) -> CompletedTrades:
        """Check if stop loss condition met

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        # Return 'completed_list' unamended if no net position or no stop loss set
        if len(self.open_trades) == 0 or self.stop_method == "no_stop":
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
        record: dict[str, Decimal | datetime],
    ) -> CompletedTrades:
        """Check whether take profit condition is met and update completed_list.

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        ent_sig = record["entry_signal"]
        ex_sig = record["exit_signal"]
        dt = record["date"]
        close = record["close"]

        # Return 'completed_list' unamended if no open position or not exit signals
        if len(self.open_trades) == 0 or ex_sig not in {"sell", "buy"}:
            return completed_list

        # Get standard 'entry_action' from 'self.open_trades'
        entry_action = get_std_field(self.open_trades, "entry_action")

        # Exit all open position in order to flip position
        # If entry_action == 'buy', then ex_sig must be 'sell'
        # ex_sig != entry_action
        if ex_sig == ent_sig and ex_sig != entry_action:
            completed_list.extend(self.exit_all(dt, close))
        else:
            completed_list.extend(self.take_profit(dt, ex_sig, close))

        return completed_list

    def check_trailing_profit(
        self,
        completed_list: CompletedTrades,
        record: dict[str, Decimal | datetime],
    ) -> CompletedTrades:
        """Check if stop loss condition met

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        # Return 'completed_list' unamended if no net position or
        # no trailing method set
        if len(self.open_trades) == 0 or self.trail_method == "no_trail":
            return completed_list

        # Update trailing profit
        trail_price = self.cal_trailing_profit(record)

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
        record: dict[str, Decimal | datetime],
    ) -> None:
        """Create new open position based on 'self.entry_struct' method.

        Args:
            ticker (str):
                Stock ticker to be traded.
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.

        Returns:
            None.
        """

        dt = record["date"]
        ent_sig = record["entry_signal"]

        # Set entry price as closing price
        entry_price = record["close"]

        if ent_sig not in {"buy", "sell"}:
            # No entry signal
            return

        # Get initialized instance of concrete class implementation
        entry_instance = get_class_instance(
            self.entry_struct,
            self.module_paths.get(self.entry_struct),
            num_lots=self.num_lots,
        )

        # Update 'self.open_trades' with new open position
        self.open_trades = entry_instance.open_new_pos(
            self.open_trades, ticker, dt, ent_sig, entry_price
        )

        if len(self.open_trades) == 0:
            raise ValueError("No open positions created!")

    def cal_trailing_profit(self, record: dict[str, Decimal | datetime]) -> None:
        """Compute trailing profit price to protect profit."""

        if self.trail_profit_inst is None:
            self.trail_profit_inst = get_class_instance(
                self.trail_method,
                self.module_paths.get(self.trail_method),
                trigger_trail=self.trigger_trail,
                step=self.step,
            )

        return self.trail_profit_inst.cal_trail_price(self.open_trades, record)

    def take_profit(
        self,
        dt: datetime,
        ex_sig: PriceAction,
        exit_price: float,
    ) -> CompletedTrades:
        """Close existing open positions based on 'self.exit_struct' method.

        Args:
            dt (datetime):
                Trade datetime object.
            ex_sig (PriceAction):
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

        if (ex_sig == "buy" and entry_action == "buy") or (
            ex_sig == "sell" and entry_action == "sell"
        ):
            # No completed trades if exit signal is same as entry action
            return []

        # Get initialized instance of concrete class implementation
        exit_instance = get_class_instance(
            self.exit_struct, self.module_paths.get(self.exit_struct)
        )

        # Update open trades and generate completed trades
        self.open_trades, completed_list = exit_instance.close_pos(
            self.open_trades, dt, exit_price
        )

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

        # Get initialized instance of concrete class implementation
        take_all_exit = get_class_instance(
            "TakeAllExit", self.module_paths.get("TakeAllExit")
        )

        # Update open trades and generate completed trades
        self.open_trades, completed_list = take_all_exit.close_pos(
            self.open_trades, dt, exit_price
        )

        if len(self.open_trades) != 0:
            raise ValueError("Open positions are not closed completely.")

        # Reset trailing profit attribute in 'self.trail_profit_inst
        self.reset_price_levels()

        return completed_list

    def cal_stop_price(self) -> Decimal:
        """Compute price to trigger stop loss."""

        if self.stop_loss_inst is None:
            self.stop_loss_inst = get_class_instance(
                self.stop_method,
                self.module_paths.get(self.stop_method),
                percent_loss=self.percent_loss,
            )

        return self.stop_loss_inst.cal_exit_price(self.open_trades)

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

    def _get_module_paths(main_pkg: str = "strat_backtest") -> dict[str, str]:
        """Convert file path to package path that can be used as input to importlib.

        Args:
            script_path (str):
                Relative path to python script containig required module.
            main_pkg (str):
                Name of main package to generate module path (Default: "strat_backtest").

        Returns:
            module_info (dict[str, str]):
                Dictionary mapping each concrete class to module path.
        """

        # Get main package directory path
        main_pkg_path = Path(__file__).parents[1]

        # Get list of folder paths containin concrete implementation of 'EntryStruc',
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
                # Omit suffixes if any
                file_name = file_path.stem
                folder_name = folder.stem

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
        record: dict[str, Decimal | datetime],
        trigger_price: Decimal,
        exit_type: ExitType,
    ) -> tuple[bool, Decimal]:
        """Check if either trailing profit or stop loss price is triggered.

        Args:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (dict[str, Decimal | datetime]):
                Dictionary mapping required attributes to its values.
            trigger_price (Decimal):
                Either trailing profit or stop loss price.
            exit_type (ExitType):
                Whether exit position due to stop loss or trailing profit
                being triggered.

        Returns:
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            trigger_info (dict[str, datetime | Decimal]):
                Dictionary containing datetime, trigger price and whether triggered.
        """

        dt = record["date"]
        close = record["close"]
        low = record["low"]
        high = record["high"]

        # Get standard 'entry_action' from 'self.open_trades'; and stop price
        entry_action = get_std_field(self.open_trades, "entry_action")

        # List of exit conditions
        cond_list = [
            self.monitor_close and entry_action == "buy" and close < trigger_price,
            self.monitor_close and entry_action == "sell" and close > trigger_price,
            not self.monitor_close and entry_action == "buy" and low < trigger_price,
            not self.monitor_close and entry_action == "sell" and high > trigger_price,
        ]

        # Actual exit price is closing price if monitor based on closing price
        # else exit price
        exit_price = close if self.monitor_close else trigger_price

        # Exit all open positions if any condition in 'cond_list' is true
        if any(cond_list):
            exit_action = "sell" if entry_action == "buy" else "buy"
            print(
                f"\n{exit_type.title()} triggered -> "
                f"{exit_action} @ {exit_type} price {trigger_price}\n"
            )

            completed_list.extend(self.exit_all(dt, exit_price))
            trigger_status = Decimal("1")

        else:
            trigger_status = Decimal("0")

        trigger_info = {
            "date": dt,
            f"{exit_type}_price": trigger_price,
            f"{exit_type}_triggered": trigger_status,
        }

        return completed_list, trigger_info

    def reset_price_levels(self) -> None:
        """Set 'trailing_profit' and 'ref_price' attribute for 'self.trail_profit_inst'
        to None if applicable."""

        if self.trail_profit_inst is not None:
            self.trail_profit_inst.reset_price_levels()
