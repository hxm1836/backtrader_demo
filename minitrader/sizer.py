"""Position sizing models for MiniTrader."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .feed import DataFeed
    from .strategy import Strategy


class Sizer:
    """Base class for position sizing."""

    def getsizing(self, strategy: Strategy, data: DataFeed, isbuy: bool) -> int:
        """Return integer order size."""
        raise NotImplementedError


@dataclass
class FixedSizer(Sizer):
    """Always return a fixed number of shares."""

    stake: int = 1

    def getsizing(self, strategy: Strategy, data: DataFeed, isbuy: bool) -> int:
        return max(0, int(self.stake))


@dataclass
class PercentSizer(Sizer):
    """Size order by percentage of current available cash."""

    percent: float = 0.95

    def getsizing(self, strategy: Strategy, data: DataFeed, isbuy: bool) -> int:
        if self.percent <= 0:
            return 0

        try:
            price = float(data.close[0])
        except Exception:
            return 0

        if price <= 0:
            return 0

        alloc_cash = strategy.broker.cash * float(self.percent)
        denom = price * (1.0 + strategy.broker.commission) if isbuy else price
        if denom <= 0:
            return 0
        return max(0, int(alloc_cash // denom))
