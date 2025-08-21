"""Abstract class used to generate various exit stuctures."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd
from pydantic import ValidationError

from strat_backtest.base.stock_trade import StockTrade
from strat_backtest.utils.constants import ClosedPositionResult, OpenTrades
from strat_backtest.utils.pos_utils import (
    gen_completed_trade,
    get_net_pos,
    validate_completed_trades,
)
from strat_backtest.utils.utils import convert_to_decimal

if TYPE_CHECKING:
    from strat_backtest.utils.constants import CompletedTrades


class ExitStruct(ABC):
    """Abstract class to populate 'StockTrade' pydantic object to close
    existing open positions fully or partially.

    - Exit open position with either profit or loss.
    - Incorporates fixed percentage gain and percentage loss.

    Args:
        None.

    Attributes:
        None.
    """

    @abstractmethod
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

        ...

    def _update_pos(
        self,
        trade: StockTrade,
        dt: datetime,
        exit_price: float | Decimal,
        exit_lots: int | None = None,
    ) -> StockTrade:
        """Update existing StockTrade objects (still open).

        Args:
            trade (StockTrade):
                Existing StockTrade object for open trade.
            dt (datetime):
                Trade datetime object.
            exit_price (float):
                Exit price of stock ticker.
            exit_lots (int | None):
                If provided, number of lot to exit open position.

        Returns:
            (StockTrade): StockTrade object updated with exit info
        """

        # Validate exit lots are not more than entry lots
        exit_lots = self._validate_exit_lots(trade, exit_lots)

        # Convert 'dt' to datetime type
        if isinstance(dt, pd.Timestamp):
            dt = dt.to_pydatetime()

        # Get exit action to update position
        exit_action = "sell" if trade.entry_action == "buy" else "buy"
        updated_trade = trade.model_copy()

        try:
            updated_trade.exit_datetime = dt
            updated_trade.exit_action = exit_action
            updated_trade.exit_lots = exit_lots
            updated_trade.exit_price = convert_to_decimal(exit_price)

            return updated_trade

        except ValidationError as e:
            print(f"Validation Error : {e}")
            return trade

    def _validate_exit_lots(
        self, trade: StockTrade, exit_lots: Decimal | None
    ) -> Decimal:
        """Ensure exit lots are not more than entry lots."""

        exit_lots = exit_lots or trade.entry_lots
        entry_lots = trade.entry_lots

        if exit_lots > entry_lots:
            raise ValueError(
                f"Exit lots ({exit_lots}) are more than entry lots ({entry_lots})"
            )

        if exit_lots < 0:
            raise ValueError(f"Exit lots ({exit_lots}) cannot be negative")

        return exit_lots


class HalfExitStruct(ExitStruct, ABC):
    """Abstract class to populate 'StockTrade' pydantic object to close
    half of existing open positions when exit conditions are met.

    Args:
        None.

    Attributes:
        None.
    """

    def _update_half_status(
        self,
        open_trades: OpenTrades | list[StockTrade],
        dt: datetime,
        exit_price: float,
    ) -> ClosedPositionResult:
        """Update open positions and completed trades after closing half of
        existing positions.

        Args:
            open_trades (OpenTrades | list[StockTrade]):
                list of 'StockTrade' pydantic objects containing trade info.
            dt (datetime):
                Trade datetime object.
            exit_price (float):
                Exit price of stock ticker.

        Returns:
            new_open_trades (OpenTrades):
                Updated deque list of 'StockTrade' objects.
            completed_trades (CompletedTrades):
                List of dictionary containing required fields to generate DataFrame.
        """

        completed_trades = []
        new_open_trades = deque()

        # Fixed ordering by converting to tuple
        open_trades = tuple(open_trades)

        # Get net position and half of net position from 'open_trades'
        net_pos = get_net_pos(open_trades)
        half_pos = math.ceil(abs(net_pos) / 2)

        for trade in open_trades:
            entry_lots = trade.entry_lots
            exit_lots = trade.exit_lots

            # Get number of open lots in 'trade'
            open_lots = entry_lots - exit_lots
            lots_to_exit = min(open_lots, half_pos)

            # Existing open position already reduced by half
            if half_pos <= 0:
                new_open_trades.append(trade.model_copy())

            # Current trade closed completedly
            elif open_lots <= half_pos:
                completed_trades = self._update_completed_trades(
                    completed_trades, trade.model_copy(), dt, exit_price, lots_to_exit
                )

            # Current trade close partially
            elif open_lots > half_pos:
                completed_trades = self._update_completed_trades(
                    completed_trades, trade.model_copy(), dt, exit_price, lots_to_exit
                )
                new_open_trades.append(
                    self._update_pos(
                        trade.model_copy(),
                        dt,
                        exit_price,
                        lots_to_exit + exit_lots,
                    )
                )

            # Reduce 'half_pos' by number of lots exited
            half_pos -= lots_to_exit

        return new_open_trades, completed_trades

    def _update_completed_trades(
        self,
        completed_trades: CompletedTrades,
        trade: StockTrade,
        dt: datetime,
        exit_price: Decimal,
        exit_lots: Decimal,
    ) -> CompletedTrades:
        """Update 'completed_trades' with completed trade info"""

        completed_trade = self._update_pos(
            trade.model_copy(), dt, exit_price, exit_lots
        )

        # Ensure entry_lots equals to exit_lots
        completed_trades.append(gen_completed_trade(completed_trade, exit_lots))

        return completed_trades
