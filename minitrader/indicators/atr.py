"""ATR indicator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feed import DataFeed
from ..indicator import Indicator


class ATR(Indicator):
    """Average True Range."""

    def __init__(self, data: DataFeed, period: int = 14) -> None:
        if not isinstance(data, DataFeed):
            raise TypeError("ATR requires a DataFeed input with high/low/close.")
        super().__init__(data=data, period=period)

    def calculate(self) -> None:
        high = np.asarray(self.data.high.values, dtype=float)
        low = np.asarray(self.data.low.values, dtype=float)
        close = np.asarray(self.data.close.values, dtype=float)
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]

        tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
        atr = pd.Series(tr).rolling(self.period, min_periods=self.period).mean().to_numpy(dtype=float)
        self._set_line("atr", atr, main=True)
