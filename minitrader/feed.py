"""Data feed abstractions for MiniTrader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator, Optional

import pandas as pd

from .utils import LineSeries


class DataFeed(Iterator["DataFeed"]):
    """Base data feed backed by a pandas DataFrame of OHLCV bars."""

    REQUIRED_COLUMNS = ("datetime", "open", "high", "low", "close", "volume")

    def __init__(self, data: pd.DataFrame) -> None:
        df = data.copy()
        self._validate_and_normalize(df)
        self._df: pd.DataFrame = df.reset_index(drop=True)
        self._idx: int = -1

        self._datetime = LineSeries(self._df["datetime"].to_numpy())
        self._open = LineSeries(self._df["open"].to_numpy())
        self._high = LineSeries(self._df["high"].to_numpy())
        self._low = LineSeries(self._df["low"].to_numpy())
        self._close = LineSeries(self._df["close"].to_numpy())
        self._volume = LineSeries(self._df["volume"].to_numpy())
        self._lines = (
            self._datetime,
            self._open,
            self._high,
            self._low,
            self._close,
            self._volume,
        )

    @classmethod
    def _validate_and_normalize(cls, df: pd.DataFrame) -> None:
        rename_map = {col: col.strip().lower() for col in df.columns}
        df.rename(columns=rename_map, inplace=True)

        missing = [c for c in cls.REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        df["datetime"] = pd.to_datetime(df["datetime"])
        for col in ("open", "high", "low", "close", "volume"):
            df[col] = pd.to_numeric(df[col], errors="raise")

    @property
    def datetime(self) -> LineSeries:
        return self._datetime

    @property
    def open(self) -> LineSeries:
        return self._open

    @property
    def high(self) -> LineSeries:
        return self._high

    @property
    def low(self) -> LineSeries:
        return self._low

    @property
    def close(self) -> LineSeries:
        return self._close

    @property
    def volume(self) -> LineSeries:
        return self._volume

    def __len__(self) -> int:
        return len(self._df)

    def advance(self) -> bool:
        """Move internal pointer forward by one bar.

        Returns ``True`` if advanced successfully, else ``False`` at end of data.
        """
        if self._idx + 1 >= len(self._df):
            return False
        self._idx += 1
        for line in self._lines:
            line.set_idx(self._idx)
        return True

    def __iter__(self) -> "DataFeed":
        return self

    def __next__(self) -> "DataFeed":
        if self.advance():
            return self
        raise StopIteration


class CSVFeed(DataFeed):
    """Data feed loaded from a CSV file."""

    def __init__(
        self,
        filepath: str | Path,
        date_col: str = "datetime",
        date_format: Optional[str] = None,
        **read_csv_kwargs: Any,
    ) -> None:
        path = Path(filepath)
        df = pd.read_csv(path, **read_csv_kwargs)
        date_col_match = None
        for col in df.columns:
            if col == date_col or col.lower() == date_col.lower():
                date_col_match = col
                break
        if date_col_match is None:
            raise ValueError(f"Date column '{date_col}' not found in CSV.")

        if date_col_match != "datetime":
            df = df.rename(columns={date_col_match: "datetime"})

        if date_format:
            df["datetime"] = pd.to_datetime(df["datetime"], format=date_format)
        else:
            df["datetime"] = pd.to_datetime(df["datetime"])

        super().__init__(df)


class PandasFeed(DataFeed):
    """Data feed created directly from an in-memory DataFrame."""

    def __init__(
        self,
        data: pd.DataFrame,
        date_col: str = "datetime",
        date_format: Optional[str] = None,
    ) -> None:
        df = data.copy()
        date_col_match = None
        for col in df.columns:
            if col == date_col or col.lower() == date_col.lower():
                date_col_match = col
                break
        if date_col_match is None:
            raise ValueError(f"Date column '{date_col}' not found in DataFrame.")

        if date_col_match != "datetime":
            df = df.rename(columns={date_col_match: "datetime"})

        if date_format:
            df["datetime"] = pd.to_datetime(df["datetime"], format=date_format)
        else:
            df["datetime"] = pd.to_datetime(df["datetime"])

        super().__init__(df)
