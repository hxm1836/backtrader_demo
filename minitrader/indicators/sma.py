"""Simple Moving Average indicator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feed import DataFeed
from ..indicator import Indicator
from ..utils import LineSeries


class SMA(Indicator):
    """Simple Moving Average."""

    def __init__(self, data: DataFeed | LineSeries | Indicator, period: int) -> None:
        super().__init__(data=data, period=period)

    def calculate(self) -> None:
        src = self.to_array(self.data)
        out = pd.Series(src).rolling(self.period, min_periods=self.period).mean().to_numpy(dtype=float)
        self._set_line("sma", out, main=True)
