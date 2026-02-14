"""Bollinger Bands indicator."""

from __future__ import annotations

import pandas as pd

from ..feed import DataFeed
from ..indicator import Indicator
from ..utils import LineSeries


class BollingerBands(Indicator):
    """Bollinger Bands with middle, top and bottom lines."""

    def __init__(
        self,
        data: DataFeed | LineSeries | Indicator,
        period: int = 20,
        devfactor: float = 2.0,
    ) -> None:
        self.devfactor = float(devfactor)
        super().__init__(data=data, period=period)

    def calculate(self) -> None:
        src = self.to_array(self.data)
        series = pd.Series(src)
        mid = series.rolling(self.period, min_periods=self.period).mean().to_numpy(dtype=float)
        std = series.rolling(self.period, min_periods=self.period).std(ddof=0).to_numpy(dtype=float)
        top = mid + self.devfactor * std
        bot = mid - self.devfactor * std

        self._set_line("mid", mid, main=True)
        self._set_line("top", top)
        self._set_line("bot", bot)
