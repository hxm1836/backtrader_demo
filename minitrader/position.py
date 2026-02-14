"""Position model for MiniTrader."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Position:
    """Track position size and average cost.

    `size` is signed: positive for long, negative for short.
    `update(size, price)` expects signed trade size:
    - buy > 0
    - sell < 0
    """

    size: float = 0.0
    price: float = 0.0

    def update(self, size: float, price: float) -> float:
        """Apply a trade update and return realized PnL from closed quantity."""
        trade_size = float(size)
        trade_price = float(price)

        if trade_size == 0:
            return 0.0

        current_size = self.size
        realized = 0.0

        if current_size == 0:
            self.size = trade_size
            self.price = trade_price
            return 0.0

        same_direction = (current_size > 0 and trade_size > 0) or (current_size < 0 and trade_size < 0)
        if same_direction:
            total_size = current_size + trade_size
            weighted_cost = (abs(current_size) * self.price) + (abs(trade_size) * trade_price)
            self.size = total_size
            self.price = weighted_cost / abs(total_size)
            return 0.0

        close_qty = min(abs(current_size), abs(trade_size))
        if current_size > 0:
            realized = (trade_price - self.price) * close_qty
        else:
            realized = (self.price - trade_price) * close_qty

        new_size = current_size + trade_size
        self.size = new_size

        if new_size == 0:
            self.price = 0.0
        elif (current_size > 0 and new_size < 0) or (current_size < 0 and new_size > 0):
            self.price = trade_price

        return realized
