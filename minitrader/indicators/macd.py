"""MACD indicator."""

from __future__ import annotations

import pandas as pd

from ..feed import DataFeed
from ..indicator import Indicator
from ..utils import LineSeries


class MACD(Indicator):
    """Moving Average Convergence Divergence."""

    def __init__(
        self,
        data: DataFeed | LineSeries | Indicator,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> None:
        self.fast_period = int(fast_period)
        self.slow_period = int(slow_period)
        self.signal_period = int(signal_period)
        super().__init__(data=data, period=self.slow_period)

    def calculate(self) -> None:
        src = self.to_array(self.data)
        s = pd.Series(src)
        fast = s.ewm(span=self.fast_period, adjust=False).mean().to_numpy(dtype=float)
        slow = s.ewm(span=self.slow_period, adjust=False).mean().to_numpy(dtype=float)
        macd = fast - slow
        signal = pd.Series(macd).ewm(span=self.signal_period, adjust=False).mean().to_numpy(dtype=float)
        hist = macd - signal

        self._set_line("macd", macd, main=True)
        self._set_line("signal", signal)
        self._set_line("histogram", hist)
