"""Returns analyzer."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..analyzer import Analyzer


class ReturnsAnalyzer(Analyzer):
    """Analyze total, annualized and daily returns."""

    def __init__(self, strategy, equity_curve: list[tuple[Any, float]], **kwargs: Any) -> None:
        super().__init__(strategy=strategy, equity_curve=equity_curve, **kwargs)
        self._analysis: dict[str, Any] = {
            "total_return": 0.0,
            "annual_return": 0.0,
            "daily_returns": [],
        }

    def run(self) -> None:
        """Compute total return, annualized return, and daily returns."""
        values = np.asarray([v for _, v in self.equity_curve], dtype=float)
        if values.size < 2 or values[0] == 0.0:
            self._analysis = {"total_return": 0.0, "annual_return": 0.0, "daily_returns": []}
            return

        daily_returns = (values[1:] / values[:-1]) - 1.0
        total_return = float((values[-1] / values[0]) - 1.0)
        periods = len(daily_returns)
        annual_return = float((1.0 + total_return) ** (252.0 / periods) - 1.0) if periods > 0 else 0.0

        self._analysis = {
            "total_return": total_return,
            "annual_return": annual_return,
            "daily_returns": daily_returns.tolist(),
        }

    def get_analysis(self) -> dict[str, Any]:
        """Return returns analysis dictionary."""
        return self._analysis
