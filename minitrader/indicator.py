"""Indicator base abstractions for MiniTrader."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray

from .feed import DataFeed
from .utils import LineSeries


class Indicator:
    """Base indicator with line outputs and pointer-synced access."""

    def __init__(self, data: DataFeed | LineSeries | "Indicator", period: int = 1) -> None:
        self.data = data
        self.period = int(period)
        self.lines: dict[str, NDArray[np.float64]] = {}
        self._line_objs: dict[str, LineSeries] = {}
        self._main_line_name: str | None = None
        self._source_line, self._source_idx_getter = self._resolve_source(data)
        self._idx: int = self._source_idx_getter()
        self.calculate()
        self.update()

    def calculate(self) -> None:
        """Pre-calculate full indicator arrays."""
        raise NotImplementedError

    def update(self) -> None:
        """Sync indicator line pointers with source pointer."""
        self._idx = self._source_idx_getter()
        for line in self._line_objs.values():
            line.set_idx(self._idx)

    def __getitem__(self, n: int) -> float:
        """Return main line value at relative index."""
        return float(self.lineseries[n])

    @property
    def lineseries(self) -> LineSeries:
        """Return main line as LineSeries."""
        if self._main_line_name is None:
            raise ValueError("Indicator has no main line.")
        return self._line_objs[self._main_line_name]

    def get_line(self, name: str) -> LineSeries:
        """Return named output line."""
        return self._line_objs[name]

    @staticmethod
    def to_array(data: DataFeed | LineSeries | "Indicator") -> NDArray[np.float64]:
        """Extract source values as float numpy array."""
        if isinstance(data, DataFeed):
            return np.asarray(data.close.values, dtype=np.float64)
        if isinstance(data, Indicator):
            return np.asarray(data.lineseries.values, dtype=np.float64)
        if isinstance(data, LineSeries):
            return np.asarray(data.values, dtype=np.float64)
        raise TypeError(f"Unsupported indicator input type: {type(data)!r}")

    @staticmethod
    def _line_from_data(data: DataFeed | LineSeries | "Indicator") -> LineSeries:
        if isinstance(data, DataFeed):
            return data.close
        if isinstance(data, Indicator):
            return data.lineseries
        if isinstance(data, LineSeries):
            return data
        raise TypeError(f"Unsupported indicator input type: {type(data)!r}")

    @classmethod
    def _resolve_source(
        cls,
        data: DataFeed | LineSeries | "Indicator",
    ) -> tuple[LineSeries, Any]:
        source_line = cls._line_from_data(data)
        return source_line, lambda: source_line.idx

    def _set_line(self, name: str, values: NDArray[np.float64], main: bool = False) -> None:
        arr = np.asarray(values, dtype=np.float64)
        self.lines[name] = arr
        line = LineSeries(arr, idx=self._source_idx_getter())
        self._line_objs[name] = line
        setattr(self, name, line)
        if self._main_line_name is None or main:
            self._main_line_name = name
