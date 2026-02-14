"""Strategy base class for MiniTrader."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from .broker import Broker
from .feed import DataFeed
from .order import Direction, Order, OrderType
from .position import Position
from .sizer import FixedSizer, Sizer


class Strategy:
    """Base strategy with params, lifecycle hooks, and order helpers."""

    params: dict[str, Any] = {}

    class Params:
        """Expose params as dot-access object."""

        def __init__(self, values: Mapping[str, Any]) -> None:
            for key, value in values.items():
                setattr(self, key, value)

    def __init__(self, datas: list[DataFeed], broker: Broker, **kwargs: Any) -> None:
        self.datas: list[DataFeed] = datas
        self.broker: Broker = broker
        self.orders: list[Order] = []
        self.trades: list[dict[str, Any]] = []
        self.analyzers: dict[str, Any] = {}

        if not datas:
            raise ValueError("Strategy requires at least one DataFeed in datas.")

        merged_params = dict(self.params)
        merged_params.update(kwargs)
        self.p = self.Params(merged_params)

        self.data = datas[0]
        self.data0 = datas[0]
        for i, data in enumerate(datas):
            setattr(self, f"data{i}", data)
            if not hasattr(data, "_name") or getattr(data, "_name") in (None, ""):
                setattr(data, "_name", f"data{i}")

        self.sizer: Sizer = FixedSizer(stake=1)

    def start(self) -> None:
        """Called once before backtest loop starts."""

    def next(self) -> None:
        """Called on every new bar."""

    def stop(self) -> None:
        """Called once after backtest loop ends."""

    def notify_order(self, order: Order) -> None:
        """Called on order status update."""

    def notify_trade(self, trade: Any) -> None:
        """Called when a trade is closed or updated."""

    @property
    def position(self) -> Position:
        """Return current position for the primary data feed."""
        name = self._get_data_name(self.data0)
        return self.broker.positions.setdefault(name, Position())

    def buy(
        self,
        size: Optional[float] = None,
        price: Optional[float] = None,
        exectype: OrderType = Order.MARKET,
        data: Optional[DataFeed] = None,
    ) -> Order:
        """Submit a buy order."""
        target_data = data or self.data0
        final_size = self._resolve_size(size=size, data=target_data, isbuy=True)
        order = Order(
            data_name=self._get_data_name(target_data),
            order_type=exectype,
            direction=Direction.BUY,
            size=final_size,
            price=price,
        )
        return self.broker.submit_order(order)

    def sell(
        self,
        size: Optional[float] = None,
        price: Optional[float] = None,
        exectype: OrderType = Order.MARKET,
        data: Optional[DataFeed] = None,
    ) -> Order:
        """Submit a sell order."""
        target_data = data or self.data0
        final_size = self._resolve_size(size=size, data=target_data, isbuy=False)
        order = Order(
            data_name=self._get_data_name(target_data),
            order_type=exectype,
            direction=Direction.SELL,
            size=final_size,
            price=price,
        )
        return self.broker.submit_order(order)

    def close(self, data: Optional[DataFeed] = None) -> Optional[Order]:
        """Close all shares for a given data feed position."""
        target_data = data or self.data0
        name = self._get_data_name(target_data)
        pos = self.broker.positions.get(name)
        if pos is None or pos.size == 0:
            return None
        if pos.size > 0:
            return self.sell(size=abs(pos.size), data=target_data)
        return self.buy(size=abs(pos.size), data=target_data)

    def _resolve_size(self, size: Optional[float], data: DataFeed, isbuy: bool) -> float:
        if size is not None:
            return float(size)
        return float(self.sizer.getsizing(self, data, isbuy))

    @staticmethod
    def _get_data_name(data: DataFeed) -> str:
        name = getattr(data, "_name", None)
        if not name:
            raise ValueError("DataFeed has no assigned name.")
        return str(name)
