"""Stochastic oscillator indicator."""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..feed import DataFeed
from ..indicator import Indicator


class Stochastic(Indicator):
    """Stochastic oscillator (%K and %D)."""

    def __init__(self, data: DataFeed, k_period: int = 14, d_period: int = 3) -> None:
        if not isinstance(data, DataFeed):
            raise TypeError("Stochastic requires a DataFeed input with high/low/close.")
        self.k_period = int(k_period)
        self.d_period = int(d_period)
        super().__init__(data=data, period=self.k_period)

    def calculate(self) -> None:
        high = np.asarray(self.data.high.values, dtype=float)
        low = np.asarray(self.data.low.values, dtype=float)
        close = np.asarray(self.data.close.values, dtype=float)

        roll_high = pd.Series(high).rolling(self.k_period, min_periods=self.k_period).max().to_numpy(dtype=float)
        roll_low = pd.Series(low).rolling(self.k_period, min_periods=self.k_period).min().to_numpy(dtype=float)
        denom = roll_high - roll_low
        k = np.divide(
            (close - roll_low) * 100.0,
            denom,
            out=np.full(len(close), np.nan, dtype=float),
            where=denom != 0.0,
        )
        d = pd.Series(k).rolling(self.d_period, min_periods=self.d_period).mean().to_numpy(dtype=float)

        self._set_line("k", k, main=True)
        self._set_line("d", d)
