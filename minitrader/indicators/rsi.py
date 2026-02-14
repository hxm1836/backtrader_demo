"""Relative Strength Index indicator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feed import DataFeed
from ..indicator import Indicator
from ..utils import LineSeries


class RSI(Indicator):
    """Relative Strength Index."""

    def __init__(self, data: DataFeed | LineSeries | Indicator, period: int = 14) -> None:
        super().__init__(data=data, period=period)

    def calculate(self) -> None:
        src = self.to_array(self.data)
        delta = np.diff(src, prepend=src[0])
        gains = np.where(delta > 0.0, delta, 0.0)
        losses = np.where(delta < 0.0, -delta, 0.0)

        alpha = 2.0 / (self.period + 1.0)
        avg_gain = pd.Series(gains).ewm(alpha=alpha, adjust=False).mean().to_numpy(dtype=float)
        avg_loss = pd.Series(losses).ewm(alpha=alpha, adjust=False).mean().to_numpy(dtype=float)

        rs = np.divide(avg_gain, avg_loss, out=np.full_like(avg_gain, np.inf), where=avg_loss != 0.0)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        self._set_line("rsi", rsi, main=True)
