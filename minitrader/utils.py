"""Utility classes for MiniTrader."""

from __future__ import annotations

from typing import Any, Union

import numpy as np
from numpy.typing import NDArray


Comparable = Union["LineSeries", int, float, np.generic]


class LineSeries:
    """Array-like view of a data line at the current backtest pointer.

    The series exposes relative indexing:
    - ``[0]``: current bar
    - ``[-1]``: previous bar
    Positive index values are forbidden to prevent look-ahead bias.
    """

    def __init__(self, data: NDArray[Any], idx: int = -1) -> None:
        self._data: NDArray[Any] = data
        self._idx: int = idx

    def set_idx(self, idx: int) -> None:
        """Update the current pointer index."""
        self._idx = idx

    def _current(self) -> Any:
        if self._idx < 0:
            raise IndexError("No current value available. Call advance() first.")
        if self._idx >= len(self._data):
            raise IndexError("Current index is out of range for underlying data.")
        return self._data[self._idx]

    def __getitem__(self, n: int) -> Any:
        """Return value at relative index ``n`` from current pointer."""
        if not isinstance(n, int):
            raise TypeError("LineSeries index must be an integer.")
        if n > 0:
            raise IndexError("Future data access is not allowed (n must be <= 0).")

        target = self._idx + n
        if target < 0:
            raise IndexError("Requested historical value is out of range.")
        if target >= len(self._data):
            raise IndexError("Requested value is out of range.")
        return self._data[target]

    def __len__(self) -> int:
        """Return count of currently visible data points."""
        return max(0, min(self._idx + 1, len(self._data)))

    def _resolve_other(self, other: Comparable) -> Any:
        if isinstance(other, LineSeries):
            return other[0]
        return other

    def __gt__(self, other: Comparable) -> bool:
        return bool(self[0] > self._resolve_other(other))

    def __lt__(self, other: Comparable) -> bool:
        return bool(self[0] < self._resolve_other(other))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, (LineSeries, int, float, np.generic)):
            return bool(self[0] == self._resolve_other(other))
        return False

    def __ne__(self, other: object) -> bool:
        if isinstance(other, (LineSeries, int, float, np.generic)):
            return bool(self[0] != self._resolve_other(other))
        return True
