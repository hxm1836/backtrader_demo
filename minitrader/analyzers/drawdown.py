"""Drawdown analyzer."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..analyzer import Analyzer


class DrawdownAnalyzer(Analyzer):
    """Analyze drawdown depth and duration."""

    def __init__(self, strategy, equity_curve: list[tuple[Any, float]], **kwargs: Any) -> None:
        super().__init__(strategy=strategy, equity_curve=equity_curve, **kwargs)
        self._analysis: dict[str, Any] = {
            "max_drawdown": 0.0,
            "max_drawdown_duration": 0,
            "drawdown_series": [],
        }

    def run(self) -> None:
        values = np.asarray([v for _, v in self.equity_curve], dtype=float)
        if values.size == 0:
            self._analysis = {"max_drawdown": 0.0, "max_drawdown_duration": 0, "drawdown_series": []}
            return

        running_max = np.maximum.accumulate(values)
        drawdown = np.where(running_max > 0.0, 1.0 - (values / running_max), 0.0)
        max_drawdown = float(np.max(drawdown)) if drawdown.size else 0.0

        max_duration = 0
        current_duration = 0
        for dd in drawdown:
            if dd > 0.0:
                current_duration += 1
                if current_duration > max_duration:
                    max_duration = current_duration
            else:
                current_duration = 0

        self._analysis = {
            "max_drawdown": max_drawdown,
            "max_drawdown_duration": int(max_duration),
            "drawdown_series": drawdown.tolist(),
        }

    def get_analysis(self) -> dict[str, Any]:
        return self._analysis
