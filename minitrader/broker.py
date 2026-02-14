"""Simulated broker for MiniTrader."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import pandas as pd

from .order import Direction, Order, OrderStatus, OrderType
from .position import Position


class Broker:
    """Broker that manages order matching, cash, and positions."""

    def __init__(self, cash: float, commission: float = 0.001) -> None:
        self.cash: float = float(cash)
        self.commission: float = float(commission)
        self.value: float = float(cash)
        self.positions: dict[str, Position] = {}
        self._pending_orders: list[Order] = []
        self._position_entry_dt: dict[str, Any] = {}
        self._last_order_updates: list[Order] = []
        self._last_trade_updates: list[dict[str, Any]] = []

    def setcash(self, amount: float) -> None:
        """Set available cash."""
        self.cash = float(amount)
        self.value = float(amount)

    def setcommission(self, commission: float) -> None:
        """Set commission ratio (e.g. 0.001 for 0.1%)."""
        self.commission = float(commission)

    def submit_order(self, order: Order) -> Order:
        """Submit an order to the pending queue."""
        if order.size <= 0:
            order.status = OrderStatus.REJECTED
            self._last_order_updates.append(order)
            return order

        if order.order_type in {OrderType.LIMIT, OrderType.STOP} and order.price is None:
            order.status = OrderStatus.REJECTED
            self._last_order_updates.append(order)
            return order

        order.status = OrderStatus.SUBMITTED
        order.status = OrderStatus.ACCEPTED
        self._pending_orders.append(order)
        self._last_order_updates.append(order)
        return order

    def execute_pending_orders(self, current_data: Mapping[str, Any], dt: datetime) -> None:
        """Try matching all pending orders on current bar data."""
        self._last_order_updates = []
        self._last_trade_updates = []
        still_pending: list[Order] = []

        for order in self._pending_orders:
            if order.status != OrderStatus.ACCEPTED:
                continue

            bar = current_data.get(order.data_name)
            if bar is None:
                still_pending.append(order)
                continue

            open_price = self._extract_bar_value(bar, "open")
            high_price = self._extract_bar_value(bar, "high")
            low_price = self._extract_bar_value(bar, "low")

            matched_price = self._match_price(order, open_price, high_price, low_price)
            if matched_price is None:
                still_pending.append(order)
                continue

            if self._execute_order(order, matched_price, dt):
                continue

        self._pending_orders = still_pending
        close_prices = self._build_close_prices(current_data)
        self.value = self.get_value(close_prices)

    def get_value(self, current_prices: Mapping[str, float]) -> float:
        """Return account equity from current cash and position market values."""
        total_value = self.cash
        for data_name, position in self.positions.items():
            current_price = current_prices.get(data_name)
            if current_price is None:
                current_price = position.price
            total_value += position.size * float(current_price)
        return float(total_value)

    def _execute_order(self, order: Order, exec_price: float, dt: datetime) -> bool:
        size = float(order.size)
        trade_value = exec_price * size
        commission_fee = trade_value * self.commission
        position = self.positions.setdefault(order.data_name, Position())
        prev_size = position.size

        if order.direction == Direction.BUY:
            total_cost = trade_value + commission_fee
            if self.cash < total_cost:
                order.status = OrderStatus.REJECTED
                self._last_order_updates.append(order)
                return False
            self.cash -= total_cost
            signed_size = size
        else:
            self.cash += trade_value - commission_fee
            signed_size = -size

        realized = position.update(signed_size, exec_price)
        order.execute(exec_price, size, dt, commission_fee)
        self._last_order_updates.append(order)
        self._record_trade_event(
            order=order,
            dt=dt,
            prev_size=prev_size,
            new_size=position.size,
            signed_size=signed_size,
            realized=realized - commission_fee,
        )
        return True

    def consume_order_updates(self) -> list[Order]:
        """Return and clear latest order status updates."""
        updates = list(self._last_order_updates)
        self._last_order_updates = []
        return updates

    def consume_trade_updates(self) -> list[dict[str, Any]]:
        """Return and clear latest trade updates."""
        updates = list(self._last_trade_updates)
        self._last_trade_updates = []
        return updates

    @staticmethod
    def _extract_bar_value(bar: Any, field: str) -> float:
        if isinstance(bar, Mapping):
            value = bar[field]
        else:
            value = getattr(bar, field)

        if hasattr(value, "__getitem__"):
            try:
                return float(value[0])
            except Exception:
                return float(value)
        return float(value)

    @staticmethod
    def _match_price(order: Order, open_price: float, high_price: float, low_price: float) -> float | None:
        if order.order_type == OrderType.MARKET:
            return open_price

        trigger_price = float(order.price) if order.price is not None else None
        if trigger_price is None:
            return None

        if order.order_type == OrderType.LIMIT:
            if order.isbuy() and low_price <= trigger_price:
                return trigger_price
            if order.issell() and high_price >= trigger_price:
                return trigger_price
            return None

        if order.order_type == OrderType.STOP:
            if order.isbuy() and high_price >= trigger_price:
                return trigger_price
            if order.issell() and low_price <= trigger_price:
                return trigger_price
            return None

        return None

    def _build_close_prices(self, current_data: Mapping[str, Any]) -> dict[str, float]:
        prices: dict[str, float] = {}
        for data_name, bar in current_data.items():
            try:
                prices[data_name] = self._extract_bar_value(bar, "close")
            except Exception:
                continue
        return prices

    def _record_trade_event(
        self,
        order: Order,
        dt: datetime,
        prev_size: float,
        new_size: float,
        signed_size: float,
        realized: float,
    ) -> None:
        data_name = order.data_name
        if prev_size == 0 and new_size != 0:
            self._position_entry_dt[data_name] = dt

        closed_qty = 0.0
        if prev_size != 0 and ((prev_size > 0 and signed_size < 0) or (prev_size < 0 and signed_size > 0)):
            closed_qty = min(abs(prev_size), abs(signed_size))

        if closed_qty > 0:
            entry_dt = self._position_entry_dt.get(data_name, dt)
            duration_days = max(
                0.0,
                (pd.Timestamp(dt) - pd.Timestamp(entry_dt)).total_seconds() / 86400.0,
            )
            self._last_trade_updates.append(
                {
                    "data_name": data_name,
                    "pnl": float(realized),
                    "size": float(closed_qty),
                    "entry_dt": entry_dt,
                    "exit_dt": dt,
                    "duration": duration_days,
                }
            )

        if new_size == 0:
            self._position_entry_dt.pop(data_name, None)
        elif prev_size == 0 and new_size != 0:
            self._position_entry_dt[data_name] = dt
        elif (prev_size > 0 > new_size) or (prev_size < 0 < new_size):
            self._position_entry_dt[data_name] = dt
