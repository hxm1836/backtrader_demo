"""Cross-over signal indicator."""

from __future__ import annotations

import numpy as np

from ..indicator import Indicator
from ..utils import LineSeries


class CrossOver(Indicator):
    """Cross-over signal: 1 up-cross, -1 down-cross, 0 otherwise."""

    def __init__(self, line1: LineSeries | Indicator, line2: LineSeries | Indicator) -> None:
        self.line2 = line2
        super().__init__(data=line1, period=1)

    def calculate(self) -> None:
        arr1 = self.to_array(self.data)
        arr2 = self.to_array(self.line2)
        if len(arr1) != len(arr2):
            raise ValueError("CrossOver inputs must have equal length.")

        diff = arr1 - arr2
        prev = np.roll(diff, 1)
        prev[0] = 0.0
        cross = np.zeros(len(diff), dtype=float)
        cross[(prev <= 0.0) & (diff > 0.0)] = 1.0
        cross[(prev >= 0.0) & (diff < 0.0)] = -1.0
        self._set_line("cross", cross, main=True)
