"""Implementation of FixedExit class

- Concrete implementation of 'ExitStruct' abstract class
- Closed specific position based on 'entry_dt' i.e. datetime when position is opened.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd

from strat_backtest.base import ExitStruct
from strat_backtest.utils.constants import (
    ClosedPositionResult,
    OpenTrades,
    PriceAction,
    Record,
)
from strat_backtest.utils.pos_utils import (
    convert_to_decimal,
    get_std_field,
    validate_completed_trades,
)

if TYPE_CHECKING:
    from strat_backtest.base.stock_trade import StockTrade
    from strat_backtest.utils.constants import CompletedTrades


class FixedExit(ExitStruct):
    """Exit specific position based on entry date.

    - 'profit' and 'stop' are required to be present in DataFrame to be iterated.
    - Iterate through open positions to check if either profit or stop level hit
    - Update open positions with exit info and update 'open_trades'.
    - Return updated open trades and completed positions.

    Args:
        monitor_close (bool):
            Whether to monitor close price ("close") or both high and low price
            (Default: False).

    Attributes:
        monitor_close (bool):
            Whether to monitor close price ("close") or both high and low price
            (Default: False).
        pos_dict (dict[datetime, StockTrade]):
            Dictionary mapping entry datetime to StockTrade pyantic object
            for quick lookup.
        exit_levels (dict[datetime, tuple[Decimal, Decimal]]):
            Dictionary mapping entry datetime to take profit and exit level

    """

    def __init__(self, monitor_close: bool = False) -> None:
        self.monitor_close = monitor_close
        self.pos_dict = {}
        self.exit_levels = {}

    def close_pos(
        self,
        open_trades: OpenTrades,
        dt: datetime,
        exit_price: float,
        _entry_dt: datetime | None = None,
    ) -> ClosedPositionResult:
        """Update existing StockTrade objects (still open); and remove completed
        StockTrade objects in 'open_trades'.

        Args:
            open_trades (OpenTrades):
                Deque list of StockTrade pydantic object to record open trades.
            dt (datetime):
                Trade datetime object.
            exit_price (float):
                Exit price of stock ticker.
            _entry_dt (datetime | None):
                If provided, datetime when position is opened.

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' objects.
            completed_trades (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        if len(open_trades) == 0:
            # No open trades to close
            return open_trades, []

        completed_trades = []
        self.pos_dict = {trade.entry_datetime: trade for trade in open_trades}

        if (desired_trade := self.pos_dict.get(_entry_dt)) is None:
            raise KeyError(f"No open positions having entry datetime of {_entry_dt}")

        # Update desired StockTrade object to complete the trade
        updated_trade = self._update_pos(desired_trade, dt, exit_price)

        # Convert StockTrade to dictionary only if all fields are populated
        # i.e. trade completed.
        if validate_completed_trades(updated_trade):
            # Remove desired StockTrade object since it is completed
            open_trades.remove(desired_trade)
            completed_trades.append(updated_trade.model_dump())

        return open_trades, completed_trades

    def update_exit_levels(
        self,
        entry_dt: datetime | pd.Timestamp,
        entry_price: Decimal,
        stop_level: Decimal,
    ) -> None:
        """Update fixed profit and stop level when new position is created.

        Args:
            entry_dt (datetime | pd.Timestamp): Datetime when position is opened.
            entry_price (Decimal): Entry price.
            stop_level (Decimal): User defined stop loss level.

        Returns:
            None.
        """

        # 1:1 risk profit
        profit_level = 2 * entry_price - stop_level

        # Ensure entry_dt is datetime type
        entry_dt = (
            entry_dt.to_pydatetime() if isinstance(entry_dt, pd.Timestamp) else entry_dt
        )

        self.exit_levels[entry_dt] = (profit_level, stop_level)

    def check_all_stop(
        self,
        open_trades: OpenTrades,
        completed_list: CompletedTrades,
        record: Record,
    ) -> ClosedPositionResult:
        """Check all open position individually if stop loss is triggered.

        Args:
            open_trades (OpenTrades):
                Deque list of 'StockTrade' pydantic objects representing open positions.
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (Record):
                Dictionary mapping required attributes to its values.

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' pydantic objects.
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        if not open_trades:
            return deque(), completed_list

        dt = record["date"]
        close = convert_to_decimal(record["close"])
        low = convert_to_decimal(record["low"])
        high = convert_to_decimal(record["high"])

        # Get standard 'entry_action' from 'self.open_trades'; and stop price
        entry_action = get_std_field(open_trades, "entry_action")

        for entry_dt, (profit_level, stop_level) in self.exit_levels:
            # Validate profit and stop level
            self._validate(entry_action, profit_level, stop_level)

            # List of stop loss conditions
            stop_cond_list = [
                self.monitor_close and entry_action == "buy" and close < stop_level,
                self.monitor_close and entry_action == "sell" and close > stop_level,
                not self.monitor_close and entry_action == "buy" and low < stop_level,
                not self.monitor_close and entry_action == "sell" and high > stop_level,
            ]

            # Ensure position is exited first as long any stop loss conditions are met
            if any(stop_cond_list):
                open_trades, updated_list = self.close_pos(
                    open_trades, dt, stop_level, entry_dt
                )
                completed_list.extend(updated_list)

                # Remove profit and stop level once position is closed
                self.exit_levels.pop(entry_dt)

        return open_trades, completed_list

    def check_all_profit(
        self,
        open_trades: OpenTrades,
        completed_list: CompletedTrades,
        record: Record,
    ) -> ClosedPositionResult:
        """Check all open position individually if target profit is triggered.

        Args:
            open_trades (OpenTrades):
                Deque list of 'StockTrade' pydantic objects representing open positions.
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
            record (Record):
                Dictionary mapping required attributes to its values.

        Returns:
            open_trades (OpenTrades):
                Updated deque list of 'StockTrade' pydantic objects.
            completed_list (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        if not open_trades:
            return deque(), completed_list

        dt = record["date"]
        low = convert_to_decimal(record["low"])
        high = convert_to_decimal(record["high"])

        # Get standard 'entry_action' from 'self.open_trades'; and stop price
        entry_action = get_std_field(open_trades, "entry_action")

        for entry_dt, (profit_level, stop_level) in self.exit_levels:
            # Validate profit and stop level
            self._validate(entry_action, profit_level, stop_level)

            # List of profit conditions
            profit_cond_list = [
                entry_action == "buy" and high > profit_level,
                entry_action == "sell" and low < profit_level,
            ]

            # Exit position if any profit conditions are met
            if any(profit_cond_list):
                open_trades, updated_list = self.close_pos(
                    open_trades, dt, profit_level, entry_dt
                )
                completed_list.extend(updated_list)

                # Remove profit and stop level once position is closed
                self.exit_levels.pop(entry_dt)

        return open_trades, completed_list
