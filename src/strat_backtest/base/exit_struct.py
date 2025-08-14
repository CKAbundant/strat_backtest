"""Abstract class used to generate various exit stuctures."""

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
        exit_price: float,
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

        exit_lots = exit_lots or trade.entry_lots

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
            updated_trade.exit_price = Decimal(str(exit_price))

            return updated_trade

        except ValidationError as e:
            print(f"Validation Error : {e}")
            return trade


class HalfExitStruct(ExitStruct, ABC):
    """Abstract class to populate 'StockTrade' pydantic object to close
    half of existing open positions when exit conditions are met.

    Args:
        None.

    Attributes:
        None.
    """

    def _update_half_status(
        self, open_trades: tuple[StockTrade], dt: datetime, exit_price: float
    ) -> ClosedPositionResult:
        """Update open positions and completed trades after closing half of
        existing positions.

        Args:
            open_trades (tuple[StockTrade]):
                Tuple of 'StockTrade' pydantic objects containing trade info.
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

        # Get net position and half of net position from 'open_trades'
        net_pos = get_net_pos(open_trades)
        half_pos = math.ceil(abs(net_pos) / 2)

        for trade in open_trades:
            initial_exit_lots = trade.exit_lots

            # Update trade only if haven't reach half of net position
            if half_pos > 0:
                # Determine quantity to close based on 'half_pos'
                lots_to_exit = min(half_pos, trade.entry_lots - initial_exit_lots)

                # Update StockTrade objects with exit info
                trade = self._update_pos(
                    trade, dt, exit_price, initial_exit_lots + lots_to_exit
                )

                # Break loop if trade is not updated properly i.e.
                # trade.exit_lots = initial_exit_lots
                if trade.exit_lots == initial_exit_lots:
                    return open_trades, []

                # Only update 'new_open_trades' if trades are still partially closed
                if not validate_completed_trades(trade):
                    new_open_trades.append(trade)

                # Create completed trades using 'lots_to_exit'
                completed_trades.append(gen_completed_trade(trade, lots_to_exit))

                # Update remaining positions required to be closed and net position
                half_pos -= lots_to_exit

            # trade not updated
            else:
                new_open_trades.append(trade)

        return new_open_trades, completed_trades
