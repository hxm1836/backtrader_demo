"""Order models for MiniTrader."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from itertools import count
from typing import Optional


class OrderType(Enum):
    """Supported order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class Direction(Enum):
    """Supported order directions."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order lifecycle statuses."""

    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"


_ORDER_REF_COUNTER = count(1)


@dataclass
class Order:
    """Trading order with execution details and lifecycle state."""

    data_name: str
    order_type: OrderType
    direction: Direction
    size: float
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.CREATED
    executed_price: Optional[float] = None
    executed_size: float = 0.0
    executed_dt: Optional[datetime] = None
    commission: float = 0.0
    ref: int = field(default_factory=lambda: next(_ORDER_REF_COUNTER))

    def execute(self, price: float, size: float, dt: datetime, commission: float = 0.0) -> None:
        """Mark the order as fully executed."""
        self.executed_price = float(price)
        self.executed_size = float(size)
        self.executed_dt = dt
        self.commission = float(commission)
        self.status = OrderStatus.COMPLETED

    def cancel(self) -> None:
        """Cancel the order if it is still active."""
        if self.alive():
            self.status = OrderStatus.CANCELED

    def isbuy(self) -> bool:
        """Return True if this is a buy order."""
        return self.direction == Direction.BUY

    def issell(self) -> bool:
        """Return True if this is a sell order."""
        return self.direction == Direction.SELL

    def alive(self) -> bool:
        """Return True if order is not in a terminal state."""
        return self.status in {
            OrderStatus.CREATED,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
        }
