"""Simulated broker for MiniTrader."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

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
            return order

        if order.order_type in {OrderType.LIMIT, OrderType.STOP} and order.price is None:
            order.status = OrderStatus.REJECTED
            return order

        order.status = OrderStatus.SUBMITTED
        order.status = OrderStatus.ACCEPTED
        self._pending_orders.append(order)
        return order

    def execute_pending_orders(self, current_data: Mapping[str, Any], dt: datetime) -> None:
        """Try matching all pending orders on current bar data."""
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

        if order.direction == Direction.BUY:
            total_cost = trade_value + commission_fee
            if self.cash < total_cost:
                order.status = OrderStatus.REJECTED
                return False
            self.cash -= total_cost
            signed_size = size
        else:
            self.cash += trade_value - commission_fee
            signed_size = -size

        position = self.positions.setdefault(order.data_name, Position())
        position.update(signed_size, exec_price)
        order.execute(exec_price, size, dt, commission_fee)
        return True

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
